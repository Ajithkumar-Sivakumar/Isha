import uuid

from app.extensions import db
from app.enums import TransportMode
from app.models.uuid_type import UUID


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    origin_id = db.Column(UUID, db.ForeignKey("ports.id"), nullable=False)
    destination_id = db.Column(UUID, db.ForeignKey("ports.id"), nullable=False)
    transport_mode = db.Column(db.Enum(TransportMode), nullable=False)
    estimated_transit_days = db.Column(db.Integer, nullable=False)
    distance_km = db.Column(db.Numeric(10, 1), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    origin = db.relationship(
        "Port", foreign_keys=[origin_id], lazy="select"
    )
    destination = db.relationship(
        "Port", foreign_keys=[destination_id], lazy="select"
    )
