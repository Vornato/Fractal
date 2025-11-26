from datetime import datetime

from flask import Blueprint, jsonify, request, current_app, session
from flask_login import current_user, login_user, logout_user

from extensions import db
from models import User, UserStatus, PasswordResetToken
from services.excel_export import write_users_to_excel

auth_bp = Blueprint("auth", __name__)


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError("Invalid date format")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    required_fields = ["name", "email", "password"]
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    if data.get("id_number") and User.query.filter_by(id_number=data["id_number"]).first():
        return jsonify({"error": "ID number already registered"}), 409

    try:
        dob = parse_date(data.get("dob"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    user = User(
        name=data["name"],
        email=data["email"],
        phone=data.get("phone"),
        id_number=data.get("id_number"),
        gender=data.get("gender"),
        dob=dob,
        social_link=data.get("social_link"),
        city=data.get("city"),
        status=UserStatus.TEMPORARY,
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    # Log the new user in immediately
    login_user(user)
    write_users_to_excel()

    return jsonify({"user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return jsonify({"user": current_user.to_dict()})

    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # Admin fast-path: allow admin credentials without separate admin page
    if email == current_app.config.get("ADMIN_EMAIL") and password == current_app.config.get("ADMIN_PASSWORD"):
        admin_user = User.query.filter_by(email=email).first()
        if not admin_user:
            admin_user = User(
                name="Admin",
                email=email,
                status=UserStatus.PERMANENT,
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
        else:
            # keep admin password in sync with env config
            admin_user.set_password(password)
            admin_user.status = UserStatus.PERMANENT
            db.session.commit()
        login_user(admin_user, remember=True)
        session["is_admin"] = True
        return jsonify({"user": admin_user.to_dict()})

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(user, remember=True)
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    session.pop("is_admin", None)
    session.clear()
    return jsonify({"message": "Logged out"})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email required"}), 400

    user = User.query.filter_by(email=email).first()
    # Respond 200 even if user not found to avoid leaking which emails exist
    if not user:
        return jsonify({"message": "If that email exists, a reset link was sent"})

    # Invalidate previous unused tokens for this user
    PasswordResetToken.query.filter_by(user_id=user.id, used=False).delete()
    token_obj = PasswordResetToken.generate(user.id, minutes_valid=current_app.config.get("PASSWORD_RESET_TOKEN_MINUTES", 60))
    db.session.add(token_obj)
    db.session.commit()

    reset_link = f"{current_app.config.get('PASSWORD_RESET_URL_BASE')}#reset={token_obj.token}"
    # In production, send via email; here we log for local testing
    current_app.logger.info("Password reset link for %s: %s", email, reset_link)

    return jsonify({"message": "If that email exists, a reset link was sent", "reset_link": reset_link})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token_value = data.get("token")
    new_password = data.get("password") or ""
    if not token_value or not new_password:
        return jsonify({"error": "Token and password required"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "Password too short"}), 400

    token_obj = PasswordResetToken.query.filter_by(token=token_value).first()
    if not token_obj or not token_obj.is_valid():
        return jsonify({"error": "Invalid or expired token"}), 400

    user = User.query.get(token_obj.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.set_password(new_password)
    token_obj.used = True
    db.session.commit()

    return jsonify({"message": "Password reset successful"})
