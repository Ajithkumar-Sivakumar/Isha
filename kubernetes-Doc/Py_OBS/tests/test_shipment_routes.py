import json
from decimal import Decimal

from tests.factories import CustomerFactory, RouteFactory, ShipmentFactory


def test_create_customer_returns_201(client, db):
    response = client.post(
        "/api/v1/customers",
        data=json.dumps(
            {
                "companyName": "Route Test Corp",
                "contactName": "Alice",
                "contactEmail": "alice@routetest.example.com",
                "street": "1 Test Rd",
                "city": "TestCity",
                "state": "TS",
                "country": "US",
                "creditLimit": "300000",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["companyName"] == "Route Test Corp"


def test_create_customer_validation_error(client, db):
    response = client.post(
        "/api/v1/customers",
        data=json.dumps({"companyName": "Missing Fields"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["errorCode"] == "VALIDATION_ERROR"


def test_get_shipments_returns_paginated(client, db):
    ShipmentFactory()
    ShipmentFactory()

    response = client.get("/api/v1/shipments?page=0&size=10")
    assert response.status_code == 200
    data = response.get_json()
    assert "content" in data
    assert "totalElements" in data
    assert data["totalElements"] >= 2


def test_get_nonexistent_shipment_returns_404(client, db):
    response = client.get(
        "/api/v1/shipments/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data["errorCode"] == "RESOURCE_NOT_FOUND"
