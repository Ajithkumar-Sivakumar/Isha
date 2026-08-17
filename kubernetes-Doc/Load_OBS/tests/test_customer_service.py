import pytest
from decimal import Decimal

from app.enums import AccountStatus
from app.exceptions import DuplicateResourceException
from app.services import customer_service
from tests.factories import CustomerFactory


def test_create_customer_success(client, db):
    data = {
        "company_name": "New Corp",
        "contact_name": "Jane Doe",
        "contact_email": "jane@newcorp.example.com",
        "street": "456 Main St",
        "city": "Portland",
        "state": "OR",
        "country": "US",
        "credit_limit": Decimal("200000"),
    }
    customer = customer_service.create_customer(data)

    assert customer.company_name == "New Corp"
    assert customer.account_status == AccountStatus.ACTIVE
    assert Decimal(str(customer.current_balance)) == Decimal("0")


def test_create_customer_duplicate_email(client, db):
    CustomerFactory(contact_email="dup@test.example.com")

    with pytest.raises(DuplicateResourceException):
        customer_service.create_customer(
            {
                "company_name": "Dup Corp",
                "contact_name": "Dup Person",
                "contact_email": "dup@test.example.com",
                "street": "789 Test",
                "city": "TestCity",
                "state": "TS",
                "country": "US",
                "credit_limit": Decimal("100000"),
            }
        )


def test_update_customer_status(client, db):
    customer = CustomerFactory()

    updated = customer_service.update_customer_status(customer.id, "SUSPENDED")
    assert updated.account_status == AccountStatus.SUSPENDED
