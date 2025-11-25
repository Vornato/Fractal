from functools import wraps

from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user

from extensions import db
from models import User, UserStatus, EventSettings, Ticket
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
    user_ids = [u.id for u in users]
    tickets = Ticket.query.filter(Ticket.user_id.in_(user_ids)).all() if user_ids else []
    ticket_map = {t.user_id: t.to_dict() for t in tickets}
    return jsonify({"users": [user.to_dict() for user in users], "tickets": ticket_map})


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


@admin_bp.route("/users/<int:user_id>/ticket", methods=["PUT"])
@admin_required
def upsert_ticket(user_id):
    data = request.get_json() or {}
    user = User.query.get_or_404(user_id)

    ticket = Ticket.query.filter_by(user_id=user.id).first()
    if not ticket:
        ticket = Ticket(user_id=user.id)
        db.session.add(ticket)

    ticket.ticket_url = (data.get("ticket") or "").strip() or None
    ticket.qr_url = (data.get("qr") or "").strip() or None
    ticket.note = (data.get("note") or "").strip() or None
    ticket.payment_id = (data.get("payment_id") or "").strip() or None

    db.session.commit()
    return jsonify({"ticket": ticket.to_dict()})


@admin_bp.route("/users/<int:user_id>/ticket", methods=["DELETE"])
@admin_required
def delete_ticket(user_id):
    Ticket.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"message": "Ticket removed"})


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
    settings.tbc_account = data.get("tbc_account") or settings.tbc_account
    settings.bog_account = data.get("bog_account") or settings.bog_account
    settings.transfer_note = data.get("transfer_note") or settings.transfer_note
    settings.qr_url = data.get("qr_url") or settings.qr_url
    if "allowed_tiers" in data:
        settings.allowed_tiers = data.get("allowed_tiers") or []

    db.session.commit()
    return jsonify({"settings": settings.to_dict()})


@admin_bp.route("/users/export", methods=["GET"])
@admin_required
def export_users_csv():
    import csv
    from io import StringIO

    users = User.query.order_by(User.id.asc()).all()
    tickets = {t.user_id: t for t in Ticket.query.all()}

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "name",
            "email",
            "phone",
            "id_number",
            "gender",
            "dob",
            "social_link",
            "city",
            "status",
            "created_at",
            "updated_at",
            "ticket_url",
            "qr_url",
            "ticket_note",
            "ticket_payment_id",
        ]
    )
    for u in users:
        t = tickets.get(u.id)
        writer.writerow(
            [
                u.id,
                u.name,
                u.email,
                u.phone,
                u.id_number,
                u.gender,
                u.dob.isoformat() if u.dob else "",
                u.social_link,
                u.city,
                u.status.value if u.status else "",
                u.created_at.isoformat() if u.created_at else "",
                u.updated_at.isoformat() if u.updated_at else "",
                t.ticket_url if t else "",
                t.qr_url if t else "",
                t.note if t else "",
                t.payment_id if t else "",
            ]
        )

    resp = current_app.response_class(output.getvalue(), mimetype="text/csv")
    resp.headers["Content-Disposition"] = "attachment; filename=users.csv"
    return resp
