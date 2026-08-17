import logging
import random
import time
from datetime import datetime, timezone
from decimal import Decimal

from flask import g

from app.extensions import db
from app.enums import DeclarationStatus, ShipmentStatus
from app.models import CustomsDeclaration, Shipment
from app.exceptions import (
    ResourceNotFoundException,
    DuplicateResourceException,
    CustomsDeclarationException,
    InvalidStateTransitionException,
)
from sqlalchemy import func

logger = logging.getLogger(__name__)


def _generate_declaration_number():
    count = db.session.query(func.count(CustomsDeclaration.id)).scalar() or 0
    year = datetime.now(timezone.utc).year
    return f"CUS-{year}-{count + 1:06d}"


def create_declaration(shipment_id, data):
    shipment = db.session.get(Shipment, shipment_id)
    if not shipment:
        raise ResourceNotFoundException("Shipment", shipment_id)

    existing = CustomsDeclaration.query.filter_by(shipment_id=shipment_id).first()
    if existing:
        raise DuplicateResourceException("CustomsDeclaration", shipment_id)

    declaration = CustomsDeclaration(
        shipment_id=shipment_id,
        declaration_number=_generate_declaration_number(),
        declaration_type=data["declaration_type"].upper(),
        status=DeclarationStatus.PENDING,
        total_declared_value=data["total_declared_value"],
        currency=data.get("currency", "USD"),
    )
    db.session.add(declaration)
    db.session.commit()
    db.session.refresh(declaration)

    logger.info(
        "Customs declaration created",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "declarationNumber": declaration.declaration_number,
            "shipmentId": str(shipment_id),
            "service": "logistics-api",
        },
    )

    return declaration


def get_declaration(shipment_id):
    declaration = CustomsDeclaration.query.filter_by(shipment_id=shipment_id).first()
    if not declaration:
        raise ResourceNotFoundException("CustomsDeclaration", shipment_id)
    return declaration


def submit_declaration(declaration_id):
    declaration = db.session.get(CustomsDeclaration, declaration_id)
    if not declaration:
        raise ResourceNotFoundException("CustomsDeclaration", declaration_id)

    if declaration.status != DeclarationStatus.PENDING:
        raise InvalidStateTransitionException(declaration.status.value, "SUBMITTED")

    # Simulate external API call with variable latency
    roll = random.random()
    if roll < 0.7:
        delay = random.uniform(0.2, 0.5)
    elif roll < 0.9:
        delay = random.uniform(2, 5)
    else:
        delay = random.uniform(8, 10)

    logger.info(
        "Submitting customs declaration to external API",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "declarationNumber": declaration.declaration_number,
            "simulatedDelay": f"{delay:.1f}s",
            "service": "logistics-api",
        },
    )

    time.sleep(delay)

    declaration.status = DeclarationStatus.SUBMITTED
    declaration.submitted_at = datetime.now(timezone.utc)

    value = Decimal(str(declaration.total_declared_value))
    duty_rate = Decimal(str(random.uniform(0.05, 0.15)))
    declaration.duty_amount = round(value * duty_rate, 2)
    declaration.tax_amount = round(value * Decimal("0.07"), 2)

    db.session.commit()
    db.session.refresh(declaration)

    logger.info(
        "Customs declaration submitted",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "declarationNumber": declaration.declaration_number,
            "dutyAmount": str(declaration.duty_amount),
            "taxAmount": str(declaration.tax_amount),
            "service": "logistics-api",
        },
    )

    return declaration


def approve_declaration(declaration_id):
    declaration = db.session.get(CustomsDeclaration, declaration_id)
    if not declaration:
        raise ResourceNotFoundException("CustomsDeclaration", declaration_id)

    if declaration.status not in (DeclarationStatus.SUBMITTED, DeclarationStatus.UNDER_REVIEW):
        raise InvalidStateTransitionException(declaration.status.value, "APPROVED")

    declaration.status = DeclarationStatus.APPROVED
    declaration.cleared_at = datetime.now(timezone.utc)

    shipment = db.session.get(Shipment, declaration.shipment_id)
    if shipment and shipment.status == ShipmentStatus.CUSTOMS_HOLD:
        shipment.status = ShipmentStatus.CUSTOMS_CLEARED
        logger.info(
            "Shipment customs cleared via declaration approval",
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "referenceNumber": shipment.reference_number,
                "service": "logistics-api",
            },
        )

    db.session.commit()
    db.session.refresh(declaration)
    return declaration


def reject_declaration(declaration_id, reason):
    declaration = db.session.get(CustomsDeclaration, declaration_id)
    if not declaration:
        raise ResourceNotFoundException("CustomsDeclaration", declaration_id)

    if declaration.status not in (DeclarationStatus.SUBMITTED, DeclarationStatus.UNDER_REVIEW):
        raise InvalidStateTransitionException(declaration.status.value, "REJECTED")

    declaration.status = DeclarationStatus.REJECTED
    declaration.rejection_reason = reason

    db.session.commit()
    db.session.refresh(declaration)

    logger.warning(
        "Customs declaration rejected",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "declarationNumber": declaration.declaration_number,
            "reason": reason,
            "service": "logistics-api",
        },
    )

    return declaration
