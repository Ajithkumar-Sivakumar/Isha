import uuid

from app.extensions import db
from app.models.uuid_type import UUID


class ShipmentItem(db.Model):
    __tablename__ = "shipment_items"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = db.Column(UUID, db.ForeignKey("shipments.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Numeric(15, 2), nullable=False)
    length = db.Column(db.Numeric(10, 2), nullable=True)
    width = db.Column(db.Numeric(10, 2), nullable=True)
    height = db.Column(db.Numeric(10, 2), nullable=True)
    hs_code = db.Column(db.String(20), nullable=True)
    country_of_origin = db.Column(db.String(3), nullable=True)
    is_dangerous = db.Column(db.Boolean, nullable=False, default=False)
    temperature_controlled = db.Column(db.Boolean, nullable=False, default=False)
    min_temperature = db.Column(db.Float, nullable=True)
    max_temperature = db.Column(db.Float, nullable=True)

    shipment = db.relationship("Shipment", back_populates="items")
