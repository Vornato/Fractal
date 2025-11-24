from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from extensions import db
from models import User
from services.excel_export import write_users_to_excel

user_bp = Blueprint("user", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format")


@user_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": current_user.to_dict()})


@user_bp.route("/me", methods=["PATCH"])
@login_required
def update_profile():
    data = request.get_json() or {}
    allowed_fields = {"name", "phone", "id_number", "gender", "dob", "social_link", "city"}

    if "id_number" in data and data.get("id_number"):
        existing = User.query.filter(User.id_number == data["id_number"], User.id != current_user.id).first()
        if existing:
            return jsonify({"error": "ID number already in use"}), 409

    for key in allowed_fields:
        if key not in data:
            continue
        if key == "dob":
            try:
                current_user.dob = parse_date(data.get("dob"))
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
        else:
            setattr(current_user, key, data.get(key))

    db.session.commit()
    write_users_to_excel()

    return jsonify({"user": current_user.to_dict()})


@user_bp.route("/photo", methods=["POST"])
@login_required
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"error": "No file part 'photo'"}), 400

    file = request.files["photo"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{current_user.id}_{uuid4().hex}_{filename}"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    file_path = upload_folder / unique_name
    file.save(file_path)

    current_user.profile_photo_path = unique_name
    db.session.commit()
    write_users_to_excel()

    return jsonify({"photo": unique_name, "url": f"/uploads/{unique_name}"})
