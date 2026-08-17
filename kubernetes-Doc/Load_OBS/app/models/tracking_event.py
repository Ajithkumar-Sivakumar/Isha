import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.enums import ShipmentStatus
from app.models.uuid_type import UUID


class TrackingEvent(db.Model):
    __tablename__ = "tracking_events"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = db.Column(UUID, db.ForeignKey("shipments.id"), nullable=False)
    status = db.Column(db.Enum(ShipmentStatus), nullable=False)
    location = db.Column(db.String(300), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    reported_by = db.Column(db.String(100), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    shipment = db.relationship("Shipment", back_populates="tracking_events")
