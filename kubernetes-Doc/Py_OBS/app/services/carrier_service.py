import logging
from decimal import Decimal

from flask import g

from app.extensions import db
from app.models import Carrier, CarrierTransportMode, Shipment
from app.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)


def get_carrier(carrier_id):
    carrier = db.session.get(Carrier, carrier_id)
    if not carrier:
        raise ResourceNotFoundException("Carrier", carrier_id)
    return carrier


def list_carriers(mode=None, active_only=True):
    query = Carrier.query

    if active_only:
        query = query.filter(Carrier.is_active.is_(True))

    if mode:
        query = query.join(CarrierTransportMode).filter(
            CarrierTransportMode.transport_mode == mode.upper()
        )

    return query.all()


def get_carrier_shipments(carrier_id, page=0, size=20):
    _ = get_carrier(carrier_id)
    query = Shipment.query.filter_by(carrier_id=carrier_id).order_by(
        Shipment.created_at.desc()
    )
    pagination = query.paginate(page=page + 1, per_page=size, error_out=False)
    return {
        "content": pagination.items,
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
        "last": not pagination.has_next,
    }


def find_available_carriers(mode, required_capacity):
    carriers = (
        Carrier.query.join(CarrierTransportMode)
        .filter(
            CarrierTransportMode.transport_mode == mode.upper(),
            Carrier.is_active.is_(True),
        )
        .all()
    )

    required = Decimal(str(required_capacity))
    return [
        c
        for c in carriers
        if (Decimal(str(c.max_capacity_kg)) - Decimal(str(c.current_load_kg))) >= required
    ]
