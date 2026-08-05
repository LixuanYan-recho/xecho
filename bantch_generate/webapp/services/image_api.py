import requests

from ..config import API_URL, UPSTREAM_REQUEST_TIMEOUT_SECONDS, VIP_IMAGE_SIZE_MAP


PENDING_STATUSES = {"pending", "queued", "running", "processing", "in_progress", "submitted"}
SUCCESS_STATUSES = {"success", "succeeded", "completed", "done", "finished"}
FAILED_STATUSES = {"failed", "error", "canceled", "cancelled", "timeout"}


def resolve_upstream_size(model, image_size):
    return VIP_IMAGE_SIZE_MAP[image_size] if model == "gpt-image-2" else image_size


def build_image_files(images):
    return [
        ("image", (image.filename, image.stream, image.mimetype or "application/octet-stream"))
        for image in images
    ]


def _build_request_data(model, prompt, size=None, aspect_ratio=""):
    data = {"model": model, "prompt": prompt, "response_format": "url"}
    if size is not None:
        data["size"] = size
    if aspect_ratio:
        data["aspect_ratio"] = aspect_ratio
    return data


def submit_image_edit_task(api_key, model, prompt, size=None, images=None, aspect_ratio="", request_id=""):
    data = _build_request_data(model=model, prompt=prompt, size=size, aspect_ratio=aspect_ratio)
    print(
        "[UPSTREAM_REQUEST]",
        {
            "request_id": request_id,
            "model": model,
            "has_size": "size" in data,
            "size": data.get("size"),
            "has_aspect_ratio": bool(aspect_ratio),
            "image_count": len(images or []),
        },
    )
    return requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        data=data,
        files=images or [],
        timeout=UPSTREAM_REQUEST_TIMEOUT_SECONDS,
    )


def query_image_edit_task(api_key, task_id, request_id=""):
    endpoint = f"{API_URL.rstrip('/')}/{task_id}"
    return requests.get(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=UPSTREAM_REQUEST_TIMEOUT_SECONDS,
    )


def _find_first_string(payload, keys):
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_task_id(payload):
    task_id = _find_first_string(payload, ("task_id", "taskId", "request_id", "requestId", "id"))
    if task_id:
        return task_id
    if isinstance(payload, dict):
        for key in ("data", "result", "output"):
            value = payload.get(key)
            if isinstance(value, dict):
                task_id = _find_first_string(value, ("task_id", "taskId", "request_id", "requestId", "id"))
                if task_id:
                    return task_id
    return ""


def parse_task_status(payload):
    raw_status = _find_first_string(payload, ("status", "state", "task_status", "phase")).lower()
    if not raw_status:
        return "success" if normalize_image_data(payload) else "pending"
    if raw_status in SUCCESS_STATUSES:
        return "success"
    if raw_status in FAILED_STATUSES:
        return "failed"
    if raw_status in PENDING_STATUSES:
        return "pending"
    return "success" if normalize_image_data(payload) else "pending"


def extract_task_error(payload):
    if not isinstance(payload, dict):
        return ""
    for key in ("error", "message", "detail", "msg"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            nested = _find_first_string(value, ("message", "detail", "msg"))
            if nested:
                return nested
    return ""


def normalize_image_data(payload):
    candidates = []
    if isinstance(payload, dict):
        for key in ("data", "images", "output", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(value)
            elif isinstance(value, (dict, str)):
                candidates.append(value)
        if not candidates:
            candidates.append(payload)
    elif isinstance(payload, list):
        candidates.extend(payload)
    elif isinstance(payload, str):
        candidates.append(payload)

    normalized = []
    for item in candidates:
        if isinstance(item, str):
            normalized.append({"kind": "url", "url": item})
            continue
        if not isinstance(item, dict):
            continue

        url = item.get("url")
        image_url = item.get("image_url")
        kind = "base64" if any(item.get(key) for key in ("b64_json", "base64", "image_base64")) else "url"
        if not url and isinstance(image_url, dict):
            url = image_url.get("url")
        elif not url and isinstance(image_url, str):
            url = image_url
        if not url:
            for key in ("b64_json", "base64", "image_base64"):
                b64_data = item.get(key)
                if b64_data:
                    mime_type = item.get("mime_type") or item.get("content_type") or "image/png"
                    url = f"data:{mime_type};base64,{b64_data}"
                    kind = "base64"
                    break
        if url:
            normalized_item = dict(item)
            normalized_item.update({"kind": kind, "url": url})
            normalized.append(normalized_item)
    return normalized
