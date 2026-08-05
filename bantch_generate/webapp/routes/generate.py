import json
import time
import uuid
from pathlib import Path

import requests
from flask import Blueprint, request, url_for

from ..config import (
    ASYNC_MAX_WAIT_SECONDS,
    ASYNC_POLL_INTERVAL_SECONDS,
    DEFAULT_PROMPT,
    GENERATION_MODES,
    MAX_UPLOAD_IMAGE_BYTES,
    VALID_IMAGE_SIZES,
    VALID_MODELS,
)
from ..repositories import results, tasks
from ..services.image_api import (
    build_image_files,
    extract_task_error,
    extract_task_id,
    normalize_image_data,
    parse_task_status,
    query_image_edit_task,
    resolve_upstream_size,
    submit_image_edit_task,
)
from ..services.result_storage import save_result_image
from ..utils.auth import api_login_required, get_current_user
from ..utils.environment import get_environment_value
from ..utils.response import error_response, success_response


generate_bp = Blueprint("generate", __name__)


@generate_bp.get("/api/tasks/recent")
@api_login_required
def recent_tasks():
    user = get_current_user()
    task_rows = tasks.list_recent_for_user(user["id"])
    result_rows = results.list_for_task_ids([row["id"] for row in task_rows])
    results_by_task = {}
    for row in result_rows:
        results_by_task.setdefault(row["task_id"], []).append(
            {
                "kind": "url",
                "url": url_for("results.download", result_id=row["id"]),
            }
        )

    data = []
    for row in task_rows:
        data.append(
            {
                "request_id": row["request_id"],
                "task_id": row["upstream_task_id"],
                "model": row["model"],
                "prompt": row["prompt"],
                "requested_at": row["requested_at"].isoformat(),
                "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                "status": row["status"],
                "error": row["error_message"],
                "data": results_by_task.get(row["id"], []),
            }
        )
    return success_response(data=data)


@generate_bp.post("/api/generate")
@api_login_required
def generate():
    request_id = uuid.uuid4().hex
    user = get_current_user()
    model = request.form.get("model", "nano-banana-pro").strip()
    generation_mode = request.form.get("generation_mode", "custom").strip()
    mode_config = GENERATION_MODES.get(generation_mode)
    submitted_prompt = request.form.get("prompt", "").strip()
    prompt = mode_config["prompt"] if mode_config and mode_config["prompt"] else submitted_prompt
    raw_image_size = request.form.get("image_size", "").strip()
    aspect_ratio = request.form.get("aspect_ratio", "").strip()
    images = [image for image in request.files.getlist("images[]") if image and image.filename]
    image_size = raw_image_size or "2k"

    try:
        task_record_id = tasks.create(request_id, user, model, prompt)
    except Exception:
        return error_response("database unavailable", 503, request_id=request_id)

    print(
        "[REQUEST_IN]",
        {
            "request_id": request_id,
            "username": user["username"],
            "model": model,
            "key_env_var": user["api_key_env_var"],
            "received_image_size": bool(raw_image_size),
            "image_size_value": raw_image_size or None,
            "has_aspect_ratio": bool(aspect_ratio),
            "image_count": len(images),
        },
    )

    validation_error = _validate_request(model, image_size, images, generation_mode, mode_config, prompt)
    if validation_error:
        return _fail(task_record_id, validation_error, 400, request_id=request_id)

    api_key = get_environment_value(user["api_key_env_var"])
    if not api_key:
        return _fail(
            task_record_id,
            f"missing env var: {user['api_key_env_var']}",
            500,
            request_id=request_id,
        )

    size_param = None if model == "gpt-image-2-c" else resolve_upstream_size(model, image_size)
    try:
        response = submit_image_edit_task(
            api_key=api_key,
            model=model,
            prompt=prompt,
            size=size_param,
            images=build_image_files(images),
            aspect_ratio=aspect_ratio,
            request_id=request_id,
        )
    except requests.RequestException as exc:
        return _fail(task_record_id, f"upstream request failed: {exc}", 502, request_id=request_id)

    if response.status_code != 200:
        print(
            "[UPSTREAM_ERROR]",
            {"request_id": request_id, "status_code": response.status_code, "body": response.text},
        )
        return _fail(task_record_id, response.text, response.status_code, request_id=request_id)

    try:
        payload = response.json()
    except ValueError:
        return _fail(task_record_id, "upstream returned non-json response", 502, request_id=request_id)

    upstream_task_id = extract_task_id(payload)
    if not upstream_task_id:
        normalized = normalize_image_data(payload)
        if normalized:
            return _finish_success(task_record_id, user, request_id, model, prompt, normalized, payload)
        return _fail(
            task_record_id,
            "upstream response has no task id and no image data",
            502,
            request_id=request_id,
        )

    tasks.set_upstream_task_id(task_record_id, upstream_task_id)
    print("[TASK_SUBMITTED]", {"request_id": request_id, "task_id": upstream_task_id, "model": model})

    deadline = time.monotonic() + ASYNC_MAX_WAIT_SECONDS
    last_status = ""
    while time.monotonic() < deadline:
        try:
            status_response = query_image_edit_task(
                api_key=api_key,
                task_id=upstream_task_id,
                request_id=request_id,
            )
        except requests.RequestException as exc:
            return _fail(
                task_record_id,
                f"query upstream task failed: {exc}",
                502,
                request_id=request_id,
                task_id=upstream_task_id,
            )

        if status_response.status_code != 200:
            message = f"upstream task query failed: HTTP {status_response.status_code}"
            return _fail(
                task_record_id,
                message,
                status_response.status_code,
                request_id=request_id,
                task_id=upstream_task_id,
            )

        try:
            status_payload = status_response.json()
        except ValueError:
            return _fail(
                task_record_id,
                "upstream task query returned non-json response",
                502,
                request_id=request_id,
                task_id=upstream_task_id,
            )

        status = parse_task_status(status_payload)
        if status != last_status:
            print("[TASK_POLL]", {"request_id": request_id, "task_id": upstream_task_id, "status": status})
            last_status = status

        if status == "success":
            normalized = normalize_image_data(status_payload)
            if not normalized:
                return _fail(
                    task_record_id,
                    "task completed but no image data returned",
                    502,
                    request_id=request_id,
                    task_id=upstream_task_id,
                )
            return _finish_success(
                task_record_id,
                user,
                request_id,
                model,
                prompt,
                normalized,
                status_payload,
                upstream_task_id,
            )

        if status == "failed":
            message = extract_task_error(status_payload) or "upstream task failed"
            return _fail(
                task_record_id,
                message,
                502,
                request_id=request_id,
                task_id=upstream_task_id,
            )

        time.sleep(ASYNC_POLL_INTERVAL_SECONDS)

    return _fail(
        task_record_id,
        f"task timeout after {ASYNC_MAX_WAIT_SECONDS} seconds",
        504,
        request_id=request_id,
        task_id=upstream_task_id,
    )


def _validate_request(model, image_size, images, generation_mode, mode_config, prompt):
    if model not in VALID_MODELS:
        return "invalid model"
    if image_size not in VALID_IMAGE_SIZES:
        return "invalid image_size"
    if not mode_config:
        return "invalid generation_mode"
    if generation_mode == "custom" and not prompt:
        return "custom prompt is required"
    if not images:
        return "no images uploaded"
    expected_count = mode_config["image_count"]
    if expected_count is not None and len(images) != expected_count:
        return f"{generation_mode} requires exactly {expected_count} images"
    for image in images:
        image.stream.seek(0, 2)
        image_size_bytes = image.stream.tell()
        image.stream.seek(0)
        if image_size_bytes > MAX_UPLOAD_IMAGE_BYTES:
            return f"image exceeds 5 MB: {image.filename}"
    return ""


def _finish_success(task_record_id, user, request_id, model, prompt, normalized, raw_payload, upstream_task_id=None):
    raw_response_json = json.dumps(raw_payload, ensure_ascii=False, default=str)
    stored_items = []
    try:
        for index, item in enumerate(normalized, start=1):
            image_path, source_url = save_result_image(item, request_id, index)
            stored_items.append({"image_path": image_path, "source_url": source_url, "original": item})
        result_ids = results.create_many(
            task_record_id,
            user,
            prompt,
            stored_items,
            raw_response_json,
            model,
        )
        response_items = []
        for result_id, stored_item in zip(result_ids, stored_items):
            item = stored_item["original"]
            response_item = dict(item)
            response_item["url"] = url_for("results.download", result_id=result_id)
            response_item["kind"] = "url"
            response_items.append(response_item)
    except Exception as exc:
        for stored_item in stored_items:
            Path(stored_item["image_path"]).unlink(missing_ok=True)
        return _fail(
            task_record_id,
            f"result image save failed: {exc}",
            502,
            request_id=request_id,
            task_id=upstream_task_id,
        )

    tasks.complete(task_record_id, True, 200)
    print("[TASK_DONE]", {"request_id": request_id, "task_id": upstream_task_id, "image_count": len(response_items)})
    return success_response(
        data=response_items,
        request_id=request_id,
        task_id=upstream_task_id,
    )


def _fail(task_record_id, message, status, **extra):
    try:
        tasks.complete(task_record_id, False, status, str(message))
    except Exception:
        pass
    return error_response(str(message), status, **extra)
