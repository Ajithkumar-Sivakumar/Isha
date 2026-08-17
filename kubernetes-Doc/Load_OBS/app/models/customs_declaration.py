import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.enums import DeclarationStatus
from app.models.uuid_type import UUID


class CustomsDeclaration(db.Model):
    __tablename__ = "customs_declarations"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    shipment_id = db.Column(
        UUID, db.ForeignKey("shipments.id"), nullable=False, unique=True
    )
    declaration_number = db.Column(db.String(50), nullable=False, unique=True)
    declaration_type = db.Column(db.String(20), nullable=False)
    status = db.Column(
        db.Enum(DeclarationStatus), nullable=False, default=DeclarationStatus.PENDING
    )
    total_declared_value = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    duty_amount = db.Column(db.Numeric(15, 2), nullable=True)
    tax_amount = db.Column(db.Numeric(15, 2), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    cleared_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    shipment = db.relationship("Shipment", backref=db.backref("customs_declaration", uselist=False))
