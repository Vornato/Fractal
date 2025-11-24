import enum
from datetime import datetime, timedelta
import secrets

from flask_login import UserMixin
from sqlalchemy import func

from extensions import bcrypt, db


class UserStatus(str, enum.Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"
    DOOR = "door"
    DECLINED = "declined"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50))
    id_number = db.Column(db.String(100), unique=True, index=True)
    gender = db.Column(db.String(20))
    dob = db.Column(db.Date)
    social_link = db.Column(db.String(255))
    city = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum(UserStatus, name="user_status", native_enum=False, length=20),
        default=UserStatus.TEMPORARY,
        server_default=UserStatus.TEMPORARY.value,
        nullable=False,
    )
    profile_photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "id_number": self.id_number,
            "gender": self.gender,
            "dob": self.dob.isoformat() if self.dob else None,
            "social_link": self.social_link,
            "city": self.city,
            "status": self.status.value if self.status else None,
            "profile_photo_path": self.profile_photo_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    language = db.Column(db.String(10))
    event_title = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    guests = db.Column(db.Integer, default=1, server_default='1')
    tier = db.Column(db.String(50))
    payment = db.Column(db.String(50))
    payment_id = db.Column(db.String(120))
    status = db.Column(db.String(50), nullable=False, default="received", server_default="received")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "language": self.language,
            "event_title": self.event_title,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "guests": self.guests,
            "tier": self.tier,
            "payment": self.payment,
            "payment_id": self.payment_id,
            "status": self.status,
        }


class EventSettings(db.Model):
    __tablename__ = "event_settings"

    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(255))
    event_date = db.Column(db.String(255))
    face_control = db.Column(db.String(255))
    tickets_info = db.Column(db.String(255))
    ticket_categories = db.Column(db.JSON)
    location = db.Column(db.String(255))
    booking_description = db.Column(db.Text)
    event_description = db.Column(db.Text)

    def to_dict(self):
        return {
          "event_name": self.event_name,
          "event_date": self.event_date,
          "face_control": self.face_control,
          "tickets_info": self.tickets_info,
          "ticket_categories": self.ticket_categories or [],
          "location": self.location,
          "booking_description": self.booking_description,
          "event_description": self.event_description,
        }


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False, server_default="0")
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    user = db.relationship("User", backref="reset_tokens")

    @classmethod
    def generate(cls, user_id: int, minutes_valid: int = 60) -> "PasswordResetToken":
        # token is stored raw; kept short-lived. Consider hashing for production use.
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=minutes_valid)
        return cls(user_id=user_id, token=token, expires_at=expires_at)

    def is_valid(self) -> bool:
        if self.used:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
