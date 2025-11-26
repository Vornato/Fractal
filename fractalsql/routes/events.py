from flask import Blueprint, jsonify

from models import EventSettings

events_bp = Blueprint("events", __name__)


@events_bp.route("/event-settings", methods=["GET"])
def public_event_settings():
    settings = EventSettings.query.first()
    if not settings:
        return jsonify({"settings": {}})
    data = settings.to_dict()
    # Remove admin-only payment details from public response
    for key in ("tbc_account", "bog_account", "transfer_note", "qr_url"):
        data.pop(key, None)
    return jsonify({"settings": data})
