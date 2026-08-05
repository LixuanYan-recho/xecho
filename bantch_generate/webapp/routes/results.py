from pathlib import Path

from flask import Blueprint, abort, send_file

from ..config import ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..repositories import results
from ..utils.auth import get_current_user, login_required


results_bp = Blueprint("results", __name__)


@results_bp.get("/results/<int:result_id>/download")
@login_required
def download(result_id):
    result = results.get_by_id(result_id)
    if not result:
        abort(404)

    user = get_current_user()
    if result["user_id"] != user["id"] and user["role"] not in {ROLE_ADMIN, ROLE_SUPER_ADMIN}:
        abort(403)

    image_path = Path(result["image_path"] or "")
    if not image_path.is_file():
        abort(404)
    return send_file(image_path, as_attachment=False, download_name=image_path.name)

