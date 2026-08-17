import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.enums import ShipmentStatus, TransportMode, ShipmentPriority
from app.models.uuid_type import UUID


class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    reference_number = db.Column(db.String(50), nullable=False, unique=True)
    customer_id = db.Column(UUID, db.ForeignKey("customers.id"), nullable=False)
    carrier_id = db.Column(UUID, db.ForeignKey("carriers.id"), nullable=True)
    route_id = db.Column(UUID, db.ForeignKey("routes.id"), nullable=False)
    status = db.Column(
        db.Enum(ShipmentStatus), nullable=False, default=ShipmentStatus.DRAFT
    )
    transport_mode = db.Column(db.Enum(TransportMode), nullable=False)
    priority = db.Column(
        db.Enum(ShipmentPriority), nullable=False, default=ShipmentPriority.STANDARD
    )
    estimated_departure = db.Column(db.DateTime, nullable=True)
    actual_departure = db.Column(db.DateTime, nullable=True)
    estimated_arrival = db.Column(db.DateTime, nullable=True)
    actual_arrival = db.Column(db.DateTime, nullable=True)
    total_weight = db.Column(db.Numeric(15, 2), nullable=False)
    total_volume = db.Column(db.Numeric(15, 2), nullable=True)
    declared_value = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    special_instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer = db.relationship("Customer", back_populates="shipments", lazy="select")
    carrier = db.relationship("Carrier", back_populates="shipments", lazy="select")
    route = db.relationship("Route", lazy="select")
    items = db.relationship(
        "ShipmentItem",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="select",
    )
    tracking_events = db.relationship(
        "TrackingEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="TrackingEvent.occurred_at",
    )
