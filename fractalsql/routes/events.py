from flask import Blueprint, jsonify

from models import EventSettings

events_bp = Blueprint("events", __name__)


@events_bp.route("/event-settings", methods=["GET"])
def public_event_settings():
    settings = EventSettings.query.first()
    return jsonify({"settings": settings.to_dict() if settings else {}})
