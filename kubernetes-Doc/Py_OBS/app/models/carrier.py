import uuid

from app.extensions import db
from app.enums import TransportMode
from app.models.uuid_type import UUID


carrier_transport_modes = db.Table(
    "carrier_transport_modes",
    db.Column("carrier_id", UUID, db.ForeignKey("carriers.id"), primary_key=True),
    db.Column("transport_mode", db.String(20), primary_key=True),
)


class Carrier(db.Model):
    __tablename__ = "carriers"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    max_capacity_kg = db.Column(db.Numeric(15, 2), nullable=False)
    current_load_kg = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    rating = db.Column(db.Numeric(3, 1), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    transport_modes_rel = db.relationship(
        "CarrierTransportMode",
        backref="carrier",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    shipments = db.relationship("Shipment", back_populates="carrier", lazy="dynamic")

    @property
    def transport_modes(self):
        return [tm.transport_mode for tm in self.transport_modes_rel]


class CarrierTransportMode(db.Model):
    __tablename__ = "carrier_transport_modes_assoc"

    carrier_id = db.Column(UUID, db.ForeignKey("carriers.id"), primary_key=True)
    transport_mode = db.Column(db.String(20), primary_key=True)
