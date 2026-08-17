import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.enums import AccountStatus
from app.models.uuid_type import UUID


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    company_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(255), nullable=False, unique=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    street = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    account_status = db.Column(
        db.Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE
    )
    credit_limit = db.Column(db.Numeric(15, 2), nullable=False)
    current_balance = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    shipments = db.relationship("Shipment", back_populates="customer", lazy="dynamic")
