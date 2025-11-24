from flask import Blueprint, jsonify, request

from extensions import db
from models import Booking


booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json() or {}

    required = ["event_title", "name", "email", "tier", "payment", "payment_id", "guests"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        guests = int(data.get("guests", 1))
        if guests < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "guests must be a positive integer"}), 400

    booking = Booking(
        language=data.get("language"),
        event_title=data.get("event_title"),
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        guests=guests,
        tier=data.get("tier"),
        payment=data.get("payment"),
        payment_id=data.get("payment_id"),
    )
    db.session.add(booking)
    db.session.commit()

    return jsonify({"booking": booking.to_dict()}), 201
