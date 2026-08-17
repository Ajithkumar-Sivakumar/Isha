import logging

from flask import g
from sqlalchemy import or_

from app.extensions import db
from app.enums import AccountStatus
from app.models import Customer, Shipment
from app.exceptions import ResourceNotFoundException, DuplicateResourceException

logger = logging.getLogger(__name__)


def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise ResourceNotFoundException("Customer", customer_id)
    return customer


def list_customers(search=None, page=0, size=20):
    query = Customer.query

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Customer.company_name.ilike(pattern),
                Customer.contact_email.ilike(pattern),
            )
        )

    query = query.order_by(Customer.created_at.desc())
    pagination = query.paginate(page=page + 1, per_page=size, error_out=False)
    return {
        "content": pagination.items,
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
        "last": not pagination.has_next,
    }


def create_customer(data):
    existing = Customer.query.filter_by(contact_email=data["contact_email"]).first()
    if existing:
        raise DuplicateResourceException("Customer", data["contact_email"])

    customer = Customer(
        company_name=data["company_name"],
        contact_name=data["contact_name"],
        contact_email=data["contact_email"],
        contact_phone=data.get("contact_phone"),
        street=data.get("street"),
        city=data.get("city"),
        state=data.get("state"),
        country=data.get("country"),
        postal_code=data.get("postal_code"),
        credit_limit=data["credit_limit"],
        current_balance=0,
        account_status=AccountStatus.ACTIVE,
    )
    db.session.add(customer)
    db.session.commit()
    db.session.refresh(customer)

    logger.info(
        "Customer created",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "customerId": str(customer.id),
            "companyName": customer.company_name,
            "service": "logistics-api",
        },
    )

    return customer


def update_customer_status(customer_id, status_value):
    customer = get_customer(customer_id)
    customer.account_status = AccountStatus(status_value.upper())
    db.session.commit()
    db.session.refresh(customer)

    logger.info(
        "Customer status updated",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "customerId": str(customer.id),
            "newStatus": customer.account_status.value,
            "service": "logistics-api",
        },
    )

    return customer


def get_customer_shipments(customer_id, page=0, size=20):
    _ = get_customer(customer_id)
    query = Shipment.query.filter_by(customer_id=customer_id).order_by(
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
