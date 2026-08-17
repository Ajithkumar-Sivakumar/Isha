import logging
import time
from decimal import Decimal

from flask import g
from sqlalchemy import func

from app.extensions import db
from app.enums import ShipmentStatus, TransportMode
from app.models import Shipment, Carrier

logger = logging.getLogger(__name__)


def get_summary():
    logger.debug("Generating analytics summary")
    start = time.time()
    total_shipments = db.session.query(func.count(Shipment.id)).scalar() or 0

    status_counts = (
        db.session.query(Shipment.status, func.count(Shipment.id))
        .group_by(Shipment.status)
        .all()
    )
    shipments_by_status = {s.value: c for s, c in status_counts}

    mode_counts = (
        db.session.query(Shipment.transport_mode, func.count(Shipment.id))
        .group_by(Shipment.transport_mode)
        .all()
    )
    shipments_by_mode = {m.value: c for m, c in mode_counts}

    delivered = (
        Shipment.query.filter(
            Shipment.status == ShipmentStatus.DELIVERED,
            Shipment.actual_arrival.isnot(None),
            Shipment.actual_departure.isnot(None),
        ).all()
    )
    if delivered:
        total_days = sum(
            (s.actual_arrival - s.actual_departure).total_seconds() / 86400
            for s in delivered
        )
        average_transit_days = round(total_days / len(delivered), 1)
    else:
        average_transit_days = 0

    total_declared_value = (
        db.session.query(func.sum(Shipment.declared_value)).scalar() or Decimal("0")
    )

    active_carriers = (
        db.session.query(func.count(Carrier.id))
        .filter(Carrier.is_active.is_(True))
        .scalar()
        or 0
    )

    active_carrier_objects = Carrier.query.filter(Carrier.is_active.is_(True)).all()
    if active_carrier_objects:
        total_util = sum(
            (Decimal(str(c.current_load_kg)) / Decimal(str(c.max_capacity_kg))) * 100
            for c in active_carrier_objects
            if Decimal(str(c.max_capacity_kg)) > 0
        )
        avg_util = round(float(total_util) / len(active_carrier_objects), 1)
    else:
        avg_util = 0

    elapsed_ms = (time.time() - start) * 1000
    logger.info(
        "Analytics summary generated: totalShipments=%s, duration=%.0fms",
        total_shipments,
        elapsed_ms,
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "service": "logistics-api",
        },
    )
    if elapsed_ms > 1000:
        logger.warning(
            "Analytics query slow: duration=%.0fms, totalShipments=%s",
            elapsed_ms,
            total_shipments,
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "service": "logistics-api",
            },
        )

    return {
        "totalShipments": total_shipments,
        "shipmentsByStatus": shipments_by_status,
        "shipmentsByMode": shipments_by_mode,
        "averageTransitDays": average_transit_days,
        "totalDeclaredValue": float(total_declared_value),
        "activeCarriers": active_carriers,
        "averageCarrierUtilization": avg_util,
    }


def get_carrier_performance():
    """Intentionally omits null check on carrier — triggers 500 for scenario 3."""
    logger.info(
        "Generating carrier performance report",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "service": "logistics-api",
        },
    )
    shipments = Shipment.query.all()

    shipments_by_carrier = {}
    for shipment in shipments:
        carrier_name = shipment.carrier.name
        shipments_by_carrier[carrier_name] = (
            shipments_by_carrier.get(carrier_name, 0) + 1
        )

    return {
        "shipmentsByCarrier": shipments_by_carrier,
        "totalShipments": len(shipments),
    }
