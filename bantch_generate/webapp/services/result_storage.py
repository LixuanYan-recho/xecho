import base64
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

from ..config import RESULT_DOWNLOAD_TIMEOUT_SECONDS, RESULT_STORAGE_DIR


MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def save_result_image(item, request_id, index):
    url = item["url"]
    if url.startswith("data:"):
        content, content_type = _decode_data_url(url)
        source_url = None
    else:
        response = requests.get(url, timeout=RESULT_DOWNLOAD_TIMEOUT_SECONDS)
        response.raise_for_status()
        content = response.content
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        source_url = url

    extension = _resolve_extension(content_type, source_url)
    month_directory = RESULT_STORAGE_DIR / datetime.now().strftime("%Y-%m")
    month_directory.mkdir(parents=True, exist_ok=True)
    final_path = month_directory / f"{request_id}_{index:02d}{extension}"
    temporary_path = final_path.with_suffix(final_path.suffix + ".tmp")
    temporary_path.write_bytes(content)
    os.replace(temporary_path, final_path)
    return str(final_path), source_url


def _decode_data_url(data_url):
    header, encoded = data_url.split(",", 1)
    content_type = header[5:].split(";", 1)[0] or "image/png"
    return base64.b64decode(encoded), content_type.lower()


def _resolve_extension(content_type, source_url):
    if content_type in MIME_EXTENSIONS:
        return MIME_EXTENSIONS[content_type]
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return guessed
    if source_url:
        suffix = Path(urlparse(source_url).path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return suffix
    return ".png"
