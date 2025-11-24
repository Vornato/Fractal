from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user

from extensions import db
from models import User, UserStatus, EventSettings
from services.excel_export import write_users_to_excel

admin_bp = Blueprint("admin", __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        is_admin = session.get("is_admin")
        # Fallback: allow authenticated user matching configured admin email
        if not is_admin:
            admin_email = current_app.config.get("ADMIN_EMAIL")
            if current_user.is_authenticated and current_user.email == admin_email:
                is_admin = True
                session["is_admin"] = True
        # Allow Basic auth with configured admin credentials (keeps admin usable when cookies are blocked)
        if not is_admin:
            auth = request.authorization
            if auth and auth.username == current_app.config.get("ADMIN_EMAIL") and auth.password == current_app.config.get("ADMIN_PASSWORD"):
                is_admin = True
                session["is_admin"] = True
        if not is_admin:
            return jsonify(
                {
                    "error": "Admin authentication required",
                    "hint": "Missing admin session cookie or invalid admin credentials",
                }
            ), 403
        return fn(*args, **kwargs)

    return wrapper


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if email == current_app.config["ADMIN_EMAIL"] and password == current_app.config["ADMIN_PASSWORD"]:
        session["is_admin"] = True
        return jsonify({"message": "Admin logged in"})

    return jsonify({"error": "Invalid admin credentials"}), 401


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.pop("is_admin", None)
    return jsonify({"message": "Admin logged out"})


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [user.to_dict() for user in users]})


@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@admin_required
def update_status(user_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "status required"}), 400

    try:
        status_enum = UserStatus(new_status)
    except ValueError:
        return jsonify({"error": "Invalid status value"}), 400

    user = User.query.get_or_404(user_id)
    user.status = status_enum
    db.session.commit()
    try:
        write_users_to_excel()
    except Exception:
        current_app.logger.exception("Failed to export users to Excel after status update")

    return jsonify({"user": user.to_dict()})


def get_or_create_settings():
    settings = EventSettings.query.first()
    if not settings:
        settings = EventSettings()
        db.session.add(settings)
        db.session.commit()
    return settings


@admin_bp.route("/event-settings", methods=["GET"])
@admin_required
def get_event_settings():
    settings = EventSettings.query.first()
    return jsonify({"settings": settings.to_dict() if settings else {}})


@admin_bp.route("/event-settings", methods=["PUT"])
@admin_required
def update_event_settings():
    data = request.get_json() or {}
    settings = get_or_create_settings()

    settings.event_name = data.get("event_name") or settings.event_name
    settings.event_date = data.get("event_date") or settings.event_date
    settings.face_control = data.get("face_control") or settings.face_control
    settings.tickets_info = data.get("tickets_info") or settings.tickets_info
    settings.ticket_categories = data.get("ticket_categories") or settings.ticket_categories
    settings.location = data.get("location") or settings.location
    settings.booking_description = data.get("booking_description") or settings.booking_description
    settings.event_description = data.get("event_description") or settings.event_description

    db.session.commit()
    return jsonify({"settings": settings.to_dict()})
