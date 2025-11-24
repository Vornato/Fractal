from pathlib import Path

from flask import Flask, send_from_directory, request
from sqlalchemy.engine.url import make_url

from config import Config
from extensions import bcrypt, db, login_manager, migrate
from models import User, EventSettings, PasswordResetToken


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    # Ensure SQLite DB path is writable (Render: /var/data/app.db)
    try:
        db_url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
        if db_url.drivername == "sqlite" and db_url.database:
            Path(db_url.database).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = None

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        # Return JSON 401 instead of redirecting to login
        return {"error": "Unauthorized"}, 401

    # Register blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.admin import admin_bp
    from routes.booking import booking_bp
    from routes.events import events_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(booking_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")


    cors_origin = app.config.get("CORS_ORIGIN")
    allowed_origins = {
        cors_origin,
        cors_origin.replace("127.0.0.1", "localhost") if cors_origin else None,
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null",  # allow file:// origin for static admin page during local dev
    }
    allowed_origins = {o for o in allowed_origins if o}

    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and (cors_origin == "*" or origin in allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, PUT, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            resp = app.make_default_options_response()
            return add_cors_headers(resp)

    @app.after_request
    def apply_cors(response):
        return add_cors_headers(response)

    @app.route("/uploads/<path:filename>", methods=["GET"])
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200
    with app.app_context():
        # Ensure new tables (like event_settings) exist without requiring a migration step here
        EventSettings.__table__.create(db.engine, checkfirst=True)
        PasswordResetToken.__table__.create(db.engine, checkfirst=True)

    return app
