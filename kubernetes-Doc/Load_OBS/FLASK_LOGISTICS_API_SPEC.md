# Flask Logistics API - Complete Build Specification

This document contains everything needed to build a Flask/Python version of the Logistics Observability API. It mirrors the Java/Spring Boot version exactly in behavior, endpoints, data model, and observability stack.

The API models a **freight forwarding** operation. Students receive this pre-built and use observability tools (Grafana, Prometheus, Tempo, Loki) to monitor, debug, and understand production behavior.

---

## 1. Tech Stack

### Core

- **Python 3.12+**
- **Flask** - web framework (Blueprints for route organization, app factory pattern)
- **Flask-SQLAlchemy** - ORM integration
- **Flask-Migrate** - database migrations via Alembic
- **Marshmallow** + **Flask-Marshmallow** + **marshmallow-sqlalchemy** - serialization, deserialization, validation
- **Flask-CORS** - cross-origin support (for Insomnia/Postman)
- **psycopg2-binary** - PostgreSQL driver
- **python-dotenv** - environment configuration
- **Gunicorn** - production WSGI server (used in Docker)

### Observability

- **python-json-logger** - structured JSON log output
- **opentelemetry-sdk** - core OpenTelemetry SDK
- **opentelemetry-exporter-otlp-proto-http** - OTLP trace exporter
- **opentelemetry-instrumentation-flask** - auto-instrument Flask requests
- **opentelemetry-instrumentation-sqlalchemy** - auto-instrument DB queries
- **prometheus-flask-instrumentator** - Prometheus metrics at `/metrics`

### Testing

- **pytest** + **pytest-flask** - test framework
- **factory-boy** - test data factories
- **pytest-cov** - coverage reporting

### requirements.txt

```
flask
flask-sqlalchemy
flask-migrate
flask-marshmallow
marshmallow-sqlalchemy
marshmallow
flask-cors
psycopg2-binary
python-dotenv
gunicorn

python-json-logger
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-http
opentelemetry-instrumentation-flask
opentelemetry-instrumentation-sqlalchemy
opentelemetry-api
prometheus-flask-instrumentator

pytest
pytest-flask
factory-boy
pytest-cov
```

---

## 2. Project Structure

```
logistics-api/
├── app/
│   ├── __init__.py              # App factory (create_app)
│   ├── config.py                # Configuration classes (Dev, Docker, Test)
│   ├── extensions.py            # db, migrate, ma, cors instances
│   ├── models/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── carrier.py
│   │   ├── port.py
│   │   ├── route.py
│   │   ├── shipment.py
│   │   ├── shipment_item.py
│   │   ├── tracking_event.py
│   │   └── customs_declaration.py
│   ├── enums.py                 # All enum definitions
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── carrier.py
│   │   ├── port.py
│   │   ├── route.py
│   │   ├── shipment.py
│   │   ├── tracking_event.py
│   │   ├── customs_declaration.py
│   │   └── common.py           # ErrorResponse, PagedResponse schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── shipment_service.py
│   │   ├── customer_service.py
│   │   ├── carrier_service.py
│   │   ├── customs_service.py
│   │   └── analytics_service.py
│   ├── routes/
│   │   ├── __init__.py          # Register all blueprints
│   │   ├── shipments.py
│   │   ├── customers.py
│   │   ├── carriers.py
│   │   ├── ports.py
│   │   ├── routes_bp.py
│   │   ├── customs.py
│   │   └── analytics.py
│   ├── exceptions.py            # Custom exception classes
│   ├── error_handlers.py        # Global error handler registration
│   ├── middleware.py            # Correlation ID, request logging
│   ├── observability.py         # OpenTelemetry + logging setup
│   └── seed.py                  # Data seeder (CLI command)
├── migrations/                  # Alembic migrations (auto-generated)
├── tests/
│   ├── conftest.py              # Fixtures, test app factory
│   ├── factories.py             # factory-boy factories
│   ├── test_shipment_service.py
│   ├── test_customer_service.py
│   └── test_shipment_routes.py
├── config/
│   ├── prometheus.yml
│   ├── tempo-config.yml
│   ├── loki-config.yml
│   ├── promtail-config.yml
│   └── grafana/
│       └── provisioning/
│           └── datasources/
│               └── datasources.yml
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .dockerignore
├── GETTING_STARTED.md
└── run.py                       # Entry point: from app import create_app; app = create_app()
```

---

## 3. Configuration

### app/config.py

```python
import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/shipments"
    )
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://localhost:4318/v1/traces"
    )

class DockerConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@postgres:5432/shipments"
    )
    OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://tempo:4318/v1/traces"
    )

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    OTEL_EXPORTER_OTLP_ENDPOINT = None
```

### .env.example

```
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shipments
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

---

## 4. Database Models

All models use UUID primary keys. Use `sqlalchemy.dialects.postgresql.UUID` for PostgreSQL and `db.String(36)` as fallback for SQLite in tests.

### Enums (app/enums.py)

```python
import enum

class ShipmentStatus(enum.Enum):
    DRAFT = "DRAFT"
    BOOKED = "BOOKED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_AT_PORT = "ARRIVED_AT_PORT"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    CUSTOMS_CLEARED = "CUSTOMS_CLEARED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class TransportMode(enum.Enum):
    AIR = "AIR"
    OCEAN = "OCEAN"
    GROUND = "GROUND"

class ShipmentPriority(enum.Enum):
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    CRITICAL = "CRITICAL"

class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class DeclarationStatus(enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class PortType(enum.Enum):
    SEAPORT = "SEAPORT"
    AIRPORT = "AIRPORT"
    GROUND_TERMINAL = "GROUND_TERMINAL"
```

### Customer

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| company_name | String(200) | NOT NULL |
| contact_name | String(100) | NOT NULL |
| contact_email | String(255) | NOT NULL, UNIQUE |
| contact_phone | String(20) | nullable |
| street | String(255) | nullable |
| city | String(100) | nullable |
| state | String(100) | nullable |
| country | String(100) | nullable |
| postal_code | String(20) | nullable |
| account_status | Enum(AccountStatus) | NOT NULL, default=ACTIVE |
| credit_limit | Numeric(15,2) | NOT NULL |
| current_balance | Numeric(15,2) | NOT NULL, default=0 |
| created_at | DateTime | NOT NULL, default=utcnow |
| updated_at | DateTime | NOT NULL, default=utcnow, onupdate=utcnow |

### Carrier

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| name | String(200) | NOT NULL |
| code | String(20) | NOT NULL, UNIQUE |
| max_capacity_kg | Numeric(15,2) | NOT NULL |
| current_load_kg | Numeric(15,2) | NOT NULL, default=0 |
| rating | Numeric(3,1) | nullable |
| contact_email | String(255) | nullable |
| is_active | Boolean | NOT NULL, default=True |

**Relationship:** `transport_modes` - many-to-many via association table `carrier_transport_modes` (columns: `carrier_id UUID FK`, `transport_mode String/Enum`). Eagerly loaded.

### Port

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| name | String(200) | NOT NULL |
| code | String(20) | NOT NULL, UNIQUE |
| type | Enum(PortType) | NOT NULL |
| city | String(100) | NOT NULL |
| country | String(100) | NOT NULL |
| timezone | String(50) | nullable |
| latitude | Float | nullable |
| longitude | Float | nullable |

### Route

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| origin_id | UUID FK(ports.id) | NOT NULL |
| destination_id | UUID FK(ports.id) | NOT NULL |
| transport_mode | Enum(TransportMode) | NOT NULL |
| estimated_transit_days | Integer | NOT NULL |
| distance_km | Numeric(10,1) | nullable |
| is_active | Boolean | NOT NULL, default=True |

**Relationships:** `origin` and `destination` are ManyToOne to Port. Eagerly loaded.

### Shipment

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| reference_number | String(50) | NOT NULL, UNIQUE |
| customer_id | UUID FK(customers.id) | NOT NULL |
| carrier_id | UUID FK(carriers.id) | nullable |
| route_id | UUID FK(routes.id) | NOT NULL |
| status | Enum(ShipmentStatus) | NOT NULL, default=DRAFT |
| transport_mode | Enum(TransportMode) | NOT NULL |
| priority | Enum(ShipmentPriority) | NOT NULL, default=STANDARD |
| estimated_departure | DateTime | nullable |
| actual_departure | DateTime | nullable |
| estimated_arrival | DateTime | nullable |
| actual_arrival | DateTime | nullable |
| total_weight | Numeric(15,2) | NOT NULL |
| total_volume | Numeric(15,2) | nullable |
| declared_value | Numeric(15,2) | NOT NULL |
| currency | String(3) | NOT NULL, default="USD" |
| special_instructions | Text | nullable |
| created_at | DateTime | NOT NULL, default=utcnow |
| updated_at | DateTime | NOT NULL, default=utcnow, onupdate=utcnow |

**Relationships:**
- `customer` - ManyToOne to Customer, eager
- `carrier` - ManyToOne to Carrier, eager, nullable
- `route` - ManyToOne to Route, eager
- `items` - OneToMany to ShipmentItem, cascade all-delete-orphan, eager
- `tracking_events` - OneToMany to TrackingEvent, cascade all, eager

### ShipmentItem

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| shipment_id | UUID FK(shipments.id) | NOT NULL |
| description | String(500) | NOT NULL |
| quantity | Integer | NOT NULL |
| weight | Numeric(15,2) | NOT NULL |
| length | Numeric(10,2) | nullable |
| width | Numeric(10,2) | nullable |
| height | Numeric(10,2) | nullable |
| hs_code | String(20) | nullable |
| country_of_origin | String(3) | nullable |
| is_dangerous | Boolean | NOT NULL, default=False |
| temperature_controlled | Boolean | NOT NULL, default=False |
| min_temperature | Float | nullable |
| max_temperature | Float | nullable |

### TrackingEvent

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| shipment_id | UUID FK(shipments.id) | NOT NULL |
| status | Enum(ShipmentStatus) | NOT NULL |
| location | String(300) | nullable |
| notes | Text | nullable |
| reported_by | String(100) | NOT NULL |
| occurred_at | DateTime | NOT NULL |
| created_at | DateTime | NOT NULL, default=utcnow |

### CustomsDeclaration

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default=uuid4 |
| shipment_id | UUID FK(shipments.id) | NOT NULL, UNIQUE |
| declaration_number | String(50) | NOT NULL, UNIQUE |
| declaration_type | String(20) | NOT NULL (values: IMPORT, EXPORT, TRANSIT) |
| status | Enum(DeclarationStatus) | NOT NULL, default=PENDING |
| total_declared_value | Numeric(15,2) | NOT NULL |
| currency | String(3) | NOT NULL, default="USD" |
| duty_amount | Numeric(15,2) | nullable |
| tax_amount | Numeric(15,2) | nullable |
| rejection_reason | Text | nullable |
| submitted_at | DateTime | nullable |
| cleared_at | DateTime | nullable |
| created_at | DateTime | NOT NULL, default=utcnow |
| updated_at | DateTime | NOT NULL, default=utcnow, onupdate=utcnow |

---

## 5. API Endpoints

All endpoints are prefixed with `/api/v1`.

### Shipments

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| POST | `/shipments` | CreateShipmentRequest body | ShipmentResponse | 201 |
| GET | `/shipments/{id}` | UUID path param | ShipmentResponse | 200 |
| GET | `/shipments` | Query: status, customerId, carrierId, transportMode, priority, fromDate, toDate, page (0), size (20), sortBy (created_at), sortDir (desc) | PagedResponse of ShipmentSummaryResponse | 200 |
| PUT | `/shipments/{id}` | UpdateShipmentRequest body | ShipmentResponse | 200 |
| DELETE | `/shipments/{id}` | UUID path param | empty | 204 |
| POST | `/shipments/{id}/assign-carrier` | AssignCarrierRequest body | ShipmentResponse | 200 |
| POST | `/shipments/{id}/tracking-events` | CreateTrackingEventRequest body | TrackingEventResponse | 201 |
| GET | `/shipments/{id}/tracking` | UUID path param | List of TrackingEventResponse | 200 |

### Customers

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| POST | `/customers` | CreateCustomerRequest body | CustomerResponse | 201 |
| GET | `/customers/{id}` | UUID path param | CustomerResponse | 200 |
| GET | `/customers` | Query: search (optional), page (0), size (20) | PagedResponse of CustomerResponse | 200 |
| PATCH | `/customers/{id}/status` | Query param: status | CustomerResponse | 200 |
| GET | `/customers/{id}/shipments` | Query: page, size | PagedResponse of ShipmentSummaryResponse | 200 |

### Carriers

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| GET | `/carriers` | Query: mode (optional), activeOnly (default true) | List of CarrierResponse | 200 |
| GET | `/carriers/{id}` | UUID path param | CarrierResponse | 200 |
| GET | `/carriers/{id}/shipments` | Query: page, size | PagedResponse of ShipmentSummaryResponse | 200 |
| GET | `/carriers/available` | Query: mode (required), requiredCapacity (required) | List of CarrierResponse | 200 |

### Ports

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| GET | `/ports` | Query: type (optional), country (optional) | List of PortResponse | 200 |
| GET | `/ports/{id}` | UUID path param | PortResponse | 200 |

### Routes

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| GET | `/routes` | Query: origin (port code), destination (port code), mode (optional) | List of RouteResponse | 200 |
| GET | `/routes/{id}` | UUID path param | RouteResponse | 200 |

### Customs Declarations

| Method | Path | Request | Response | Status |
|--------|------|---------|----------|--------|
| POST | `/shipments/{shipmentId}/customs-declaration` | CreateCustomsDeclarationRequest body | CustomsDeclarationResponse | 201 |
| GET | `/shipments/{shipmentId}/customs-declaration` | UUID path param | CustomsDeclarationResponse | 200 |
| POST | `/customs-declarations/{id}/submit` | UUID path param | CustomsDeclarationResponse | 200 |
| POST | `/customs-declarations/{id}/approve` | UUID path param | CustomsDeclarationResponse | 200 |
| POST | `/customs-declarations/{id}/reject` | UUID path param + query: reason | CustomsDeclarationResponse | 200 |

### Analytics

| Method | Path | Response | Status |
|--------|------|----------|--------|
| GET | `/analytics/shipments/summary` | AnalyticsSummaryResponse | 200 |

### Health/Metrics (outside /api/v1)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Returns `{"status": "UP"}` |
| GET | `/metrics` | Prometheus metrics (auto-provided by prometheus-flask-instrumentator) |

---

## 6. Request/Response Schemas (Marshmallow)

### Request Schemas with Validation

**CreateShipmentRequest:**
- `customer_id`: UUID, required
- `route_id`: UUID, required
- `transport_mode`: String, required, must be one of AIR/OCEAN/GROUND
- `priority`: String, optional, default STANDARD, must be one of STANDARD/EXPRESS/CRITICAL
- `estimated_departure`: DateTime, required
- `estimated_arrival`: DateTime, required
- `total_weight`: Decimal, required, must be positive
- `total_volume`: Decimal, optional, must be positive
- `declared_value`: Decimal, required, must be positive
- `currency`: String, optional, default "USD", length must be 3
- `special_instructions`: String, optional
- `items`: Nested List of CreateShipmentItemRequest, required, min length 1

**CreateShipmentItemRequest:**
- `description`: String, required, max length 500
- `quantity`: Integer, required, must be positive
- `weight`: Decimal, required, must be positive
- `length`, `width`, `height`: Decimal, optional, must be positive
- `hs_code`: String, optional, regex pattern `^\d{4}\.\d{2}(\.\d{2})?$`
- `country_of_origin`: String, optional, 2-3 characters
- `is_dangerous`: Boolean, optional, default False
- `temperature_controlled`: Boolean, optional, default False
- `min_temperature`, `max_temperature`: Float, optional

**UpdateShipmentRequest (all fields optional):**
- `priority`: String, must be valid enum
- `estimated_departure`: DateTime
- `estimated_arrival`: DateTime
- `special_instructions`: String
- `declared_value`: Decimal, must be positive

**AssignCarrierRequest:**
- `carrier_id`: UUID, required

**CreateTrackingEventRequest:**
- `status`: String, required
- `location`: String, required, max length 300
- `notes`: String, optional
- `reported_by`: String, required
- `occurred_at`: DateTime, required

**CreateCustomerRequest:**
- `company_name`: String, required, max length 200
- `contact_name`: String, required, max length 100
- `contact_email`: String, required, must be valid email
- `contact_phone`: String, optional, max length 20
- `street`, `city`, `state`, `country`: String, required
- `postal_code`: String, optional
- `credit_limit`: Decimal, required, must be positive

**CreateCustomsDeclarationRequest:**
- `declaration_type`: String, required, must be IMPORT/EXPORT/TRANSIT
- `total_declared_value`: Decimal, required, must be positive
- `currency`: String, optional, default "USD", length 3

### Response Schemas

**PagedResponse:**
```json
{
  "content": [...],
  "page": 0,
  "size": 20,
  "totalElements": 42,
  "totalPages": 3,
  "last": false
}
```

**ShipmentResponse:**
```json
{
  "id": "uuid",
  "referenceNumber": "EXP-2026-00001",
  "customer": {
    "id": "uuid",
    "companyName": "Pacific Electronics Co."
  },
  "carrier": {
    "id": "uuid",
    "name": "Maersk Line",
    "code": "MAER"
  },
  "route": {
    "id": "uuid",
    "originPortName": "Port of Seattle",
    "originPortCode": "USSEA",
    "destinationPortName": "Port of Shanghai",
    "destinationPortCode": "CNSHA",
    "estimatedTransitDays": 14
  },
  "status": "IN_TRANSIT",
  "transportMode": "OCEAN",
  "priority": "STANDARD",
  "estimatedDeparture": "2026-07-01T08:00:00",
  "actualDeparture": "2026-07-02T06:00:00",
  "estimatedArrival": "2026-07-15T08:00:00",
  "actualArrival": null,
  "totalWeight": 12500.00,
  "totalVolume": 55.00,
  "declaredValue": 125000.00,
  "currency": "USD",
  "specialInstructions": null,
  "items": [...],
  "createdAt": "2026-05-25T12:00:00",
  "updatedAt": "2026-05-25T14:00:00"
}
```

**ShipmentSummaryResponse:**
```json
{
  "id": "uuid",
  "referenceNumber": "EXP-2026-00001",
  "customerName": "Pacific Electronics Co.",
  "carrierName": "Maersk Line",
  "status": "IN_TRANSIT",
  "transportMode": "OCEAN",
  "priority": "STANDARD",
  "originPort": "USSEA",
  "destinationPort": "CNSHA",
  "estimatedArrival": "2026-07-15T08:00:00",
  "totalWeight": 12500.00,
  "declaredValue": 125000.00,
  "createdAt": "2026-05-25T12:00:00"
}
```

**CustomerResponse:**
```json
{
  "id": "uuid",
  "companyName": "Pacific Electronics Co.",
  "contactName": "Sarah Chen",
  "contactEmail": "sarah.chen@pacelec.example.com",
  "contactPhone": "+1-206-555-0100",
  "street": "1200 Harbor Ave",
  "city": "Seattle",
  "state": "WA",
  "country": "US",
  "postalCode": "98101",
  "accountStatus": "ACTIVE",
  "creditLimit": 500000.00,
  "currentBalance": 170000.00,
  "createdAt": "...",
  "updatedAt": "..."
}
```

**CarrierResponse:**
```json
{
  "id": "uuid",
  "name": "Maersk Line",
  "code": "MAER",
  "transportModes": ["OCEAN"],
  "maxCapacityKg": 5000000.00,
  "currentLoadKg": 2100000.00,
  "availableCapacityKg": 2900000.00,
  "utilizationPercent": 42.0000,
  "rating": 4.5,
  "contactEmail": "ops@maersk.example.com",
  "isActive": true
}
```

**TrackingEventResponse:**
```json
{
  "id": "uuid",
  "shipmentId": "uuid",
  "status": "IN_TRANSIT",
  "location": "Port of Seattle, Terminal 5",
  "notes": "Departed on schedule",
  "reportedBy": "terminal-ops",
  "occurredAt": "2026-07-03T06:00:00",
  "createdAt": "..."
}
```

**CustomsDeclarationResponse:**
```json
{
  "id": "uuid",
  "shipmentId": "uuid",
  "declarationNumber": "CUS-2026-000001",
  "declarationType": "IMPORT",
  "status": "SUBMITTED",
  "totalDeclaredValue": 125000.00,
  "currency": "USD",
  "dutyAmount": 12500.00,
  "taxAmount": 8750.00,
  "rejectionReason": null,
  "submittedAt": "2026-05-25T14:30:00",
  "clearedAt": null,
  "createdAt": "...",
  "updatedAt": "..."
}
```

**AnalyticsSummaryResponse:**
```json
{
  "totalShipments": 42,
  "shipmentsByStatus": {"DRAFT": 5, "BOOKED": 10, "IN_TRANSIT": 15, ...},
  "shipmentsByMode": {"OCEAN": 30, "AIR": 8, "GROUND": 4},
  "averageTransitDays": 12.5,
  "totalDeclaredValue": 5250000.00,
  "activeCarriers": 5,
  "averageCarrierUtilization": 52.3
}
```

**ErrorResponse:**
```json
{
  "timestamp": "2026-05-25T14:00:00",
  "status": 404,
  "errorCode": "RESOURCE_NOT_FOUND",
  "message": "Shipment not found with identifier: abc-123",
  "correlationId": "uuid-string",
  "path": "/api/v1/shipments/abc-123",
  "fieldErrors": []
}
```

For validation errors, `fieldErrors` is populated:
```json
{
  "fieldErrors": [
    {"field": "contact_email", "message": "Not a valid email address.", "rejectedValue": "not-an-email"}
  ]
}
```

**IMPORTANT:** Use camelCase for all JSON response keys (configure Marshmallow to output camelCase). Request bodies also expect camelCase keys (use `data_key` in Marshmallow fields).

---

## 7. Error Handling

### Custom Exception Classes (app/exceptions.py)

```python
class ShipmentApiException(Exception):
    def __init__(self, message, error_code, status_code):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class ResourceNotFoundException(ShipmentApiException):
    def __init__(self, resource_type, identifier):
        super().__init__(
            f"{resource_type} not found with identifier: {identifier}",
            "RESOURCE_NOT_FOUND", 404
        )

class InvalidStateTransitionException(ShipmentApiException):
    def __init__(self, current_state, target_state):
        super().__init__(
            f"Cannot transition from {current_state} to {target_state}",
            "INVALID_STATE_TRANSITION", 409
        )

class CreditLimitExceededException(ShipmentApiException):
    def __init__(self, shipment_value, remaining_credit):
        super().__init__(
            f"Shipment value {shipment_value} exceeds remaining credit {remaining_credit}",
            "CREDIT_LIMIT_EXCEEDED", 422
        )

class CarrierCapacityExceededException(ShipmentApiException):
    def __init__(self, carrier_name, overflow):
        super().__init__(
            f"Carrier {carrier_name} capacity exceeded by {overflow} kg",
            "CARRIER_CAPACITY_EXCEEDED", 422
        )

class CustomerAccountSuspendedException(ShipmentApiException):
    def __init__(self, customer_id):
        super().__init__(
            f"Customer account {customer_id} is suspended",
            "ACCOUNT_SUSPENDED", 403
        )

class DuplicateResourceException(ShipmentApiException):
    def __init__(self, resource_type, identifier):
        super().__init__(
            f"{resource_type} already exists with identifier: {identifier}",
            "DUPLICATE_RESOURCE", 409
        )

class InvalidRouteException(ShipmentApiException):
    def __init__(self, origin, destination, mode):
        super().__init__(
            f"No valid route from {origin} to {destination} for mode {mode}",
            "INVALID_ROUTE", 422
        )

class CustomsDeclarationException(ShipmentApiException):
    def __init__(self, reason):
        super().__init__(reason, "CUSTOMS_DECLARATION_ERROR", 422)
```

### Global Error Handler (app/error_handlers.py)

Register these on the Flask app:

| Exception | Status | Error Code |
|-----------|--------|------------|
| `ShipmentApiException` (and subclasses) | from exception | from exception |
| `marshmallow.ValidationError` | 400 | VALIDATION_ERROR |
| `sqlalchemy.exc.IntegrityError` | 409 | DATA_INTEGRITY_VIOLATION |
| `json.JSONDecodeError` / `BadRequest` | 400 | MALFORMED_REQUEST |
| `Exception` (catch-all) | 500 | INTERNAL_ERROR |

All error responses include `correlationId` from the request context and `path` from `request.path`.

---

## 8. Business Logic

### Shipment State Machine

Valid transitions (stored as a dict in ShipmentService):

```python
VALID_TRANSITIONS = {
    ShipmentStatus.DRAFT: {ShipmentStatus.BOOKED, ShipmentStatus.CANCELLED},
    ShipmentStatus.BOOKED: {ShipmentStatus.PICKED_UP, ShipmentStatus.CANCELLED},
    ShipmentStatus.PICKED_UP: {ShipmentStatus.IN_TRANSIT},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.ARRIVED_AT_PORT},
    ShipmentStatus.ARRIVED_AT_PORT: {ShipmentStatus.CUSTOMS_HOLD, ShipmentStatus.OUT_FOR_DELIVERY},
    ShipmentStatus.CUSTOMS_HOLD: {ShipmentStatus.CUSTOMS_CLEARED},
    ShipmentStatus.CUSTOMS_CLEARED: {ShipmentStatus.OUT_FOR_DELIVERY},
    ShipmentStatus.OUT_FOR_DELIVERY: {ShipmentStatus.DELIVERED},
}
```

DELIVERED and CANCELLED are terminal states with no valid outgoing transitions.

### Shipment Creation

1. Look up customer by `customer_id`. If not found: `ResourceNotFoundException("Customer", id)`
2. If `customer.account_status != ACTIVE`: raise `CustomerAccountSuspendedException(customer.id)`
3. Compute `remaining_credit = customer.credit_limit - customer.current_balance`. If `declared_value > remaining_credit`: raise `CreditLimitExceededException(declared_value, remaining_credit)`
4. Look up route by `route_id`. If not found: `ResourceNotFoundException("Route", id)`. If `route.is_active == False`: raise `InvalidRouteException(origin_code, destination_code, transport_mode)`
5. Parse `transport_mode` (case-insensitive) and `priority` (default STANDARD)
6. Generate reference number: `EXP-{YYYY}-{00001}` (based on total shipment count + 1, zero-padded to 5 digits)
7. Create shipment with status=DRAFT
8. Create ShipmentItem records for each item in the request
9. Increment `customer.current_balance` by `declared_value`
10. Commit and return

### Shipment Update

- Only allowed when status is DRAFT or BOOKED (else raise `InvalidStateTransitionException(current_status, "UPDATE")`)
- Updatable fields (all optional): priority, estimated_departure, estimated_arrival, special_instructions, declared_value

### Shipment Cancellation

1. Validate state transition (only DRAFT/BOOKED can transition to CANCELLED)
2. If carrier is assigned: decrement `carrier.current_load_kg` by `shipment.total_weight`
3. Decrement `customer.current_balance` by `shipment.declared_value`
4. Set status to CANCELLED

### Carrier Assignment

1. Shipment must be in BOOKED status (else raise `InvalidStateTransitionException`)
2. Carrier must exist
3. Carrier must support shipment's transport_mode (else raise `InvalidRouteException` with note about incompatible mode)
4. Available capacity: `carrier.max_capacity_kg - carrier.current_load_kg`. If `shipment.total_weight > available`: raise `CarrierCapacityExceededException(carrier.name, overflow)`
5. Check if any items are dangerous goods - if so, log a warning
6. Set `shipment.carrier = carrier`
7. Increment `carrier.current_load_kg` by `shipment.total_weight`
8. Compute utilization percentage. If > 85%, log a warning

### Recording Tracking Events

1. Validate state transition from current status to new status
2. Update shipment status
3. If new status is DELIVERED: set `shipment.actual_arrival`, release carrier load
4. If new status is PICKED_UP or IN_TRANSIT and `actual_departure` is None: set `shipment.actual_departure`
5. Create TrackingEvent record

### Customer Creation

- Check email uniqueness (else `DuplicateResourceException("Customer", email)`)
- Account starts ACTIVE with current_balance=0

### Customer Status Update

- Free transition between any AccountStatus values (no state machine)

### Customs Declaration Creation

- Shipment must exist
- Only one declaration per shipment (else `DuplicateResourceException`)
- Generate declaration number: `CUS-{YYYY}-{000001}` (6-digit zero-padded, based on count + 1)
- Starts in PENDING status

### Customs Declaration Submit (PENDING -> SUBMITTED)

- Must be in PENDING status
- Simulate external API call with variable latency using `time.sleep()`:
  - 70% chance: 0.2 - 0.5 seconds (normal)
  - 20% chance: 2 - 5 seconds (slow)
  - 10% chance: 8 - 10 seconds (very slow)
- Set `submitted_at = now`
- Calculate `duty_amount = total_declared_value * random(0.05, 0.15)`
- Calculate `tax_amount = total_declared_value * 0.07`

### Customs Declaration Approve (SUBMITTED/UNDER_REVIEW -> APPROVED)

- Set `cleared_at = now`
- If associated shipment is in CUSTOMS_HOLD status, transition it to CUSTOMS_CLEARED

### Customs Declaration Reject (SUBMITTED/UNDER_REVIEW -> REJECTED)

- Set `rejection_reason` from request

### Analytics Summary

Returns:
- `totalShipments`: count of all shipments
- `shipmentsByStatus`: dict of status -> count
- `shipmentsByMode`: dict of mode -> count
- `averageTransitDays`: average of (actual_arrival - actual_departure) in days for delivered shipments
- `totalDeclaredValue`: sum of all shipment declared values
- `activeCarriers`: count of carriers where is_active=True
- `averageCarrierUtilization`: average of (current_load_kg / max_capacity_kg * 100) for active carriers

---

## 9. Observability Configuration

### Structured Logging (app/observability.py)

Use `python-json-logger` to format all log output as JSON:

```python
import logging
from pythonjsonlogger import jsonlogger

def setup_logging(app):
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "@timestamp", "levelname": "level", "name": "logger_name"},
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    logging.getLogger("app").setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
```

Each log entry should include:
- `@timestamp`
- `level`
- `logger_name`
- `message`
- `correlationId` (from context)
- `service`: "logistics-api"

### Correlation ID Middleware (app/middleware.py)

Use Flask `before_request`/`after_request` with `contextvars` or `flask.g`:

1. On each request, read `X-Correlation-ID` header. If absent, generate a UUID.
2. Store in `g.correlation_id`
3. Add to response headers: `X-Correlation-ID`
4. Use a logging filter to inject `correlationId` into all log records during the request
5. Skip for paths starting with `/health`, `/metrics`
6. Log request start: `"Request started: method={method}, path={path}, remoteAddr={ip}"`
7. Log request end: `"Request completed: method={method}, path={path}, status={status}, duration={ms}ms"`
8. If duration > 3000ms, log at WARN level

### OpenTelemetry Tracing

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_tracing(app):
    if not app.config.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return

    resource = Resource.create({"service.name": "logistics-api"})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=app.config["OTEL_EXPORTER_OTLP_ENDPOINT"])
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=db.engine)
```

### Prometheus Metrics

```python
from prometheus_flask_instrumentator import Instrumentator

def setup_metrics(app):
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

This auto-provides:
- `http_request_duration_seconds` histogram
- `http_requests_total` counter
- Standard process metrics

---

## 10. Docker Setup

### Dockerfile

```dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "run:app"]
```

### docker-compose.yml

```yaml
services:
  app:
    build: .
    ports:
      - "8080:8000"
    environment:
      - FLASK_ENV=docker
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/shipments
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318/v1/traces
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - observability
    labels:
      - "logging=promtail"

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: shipments
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - observability

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=7d'
    networks:
      - observability

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"
      - "4318:4318"
    volumes:
      - ./config/tempo-config.yml:/etc/tempo/config.yml
      - tempo_data:/var/tempo
    command: ["-config.file=/etc/tempo/config.yml"]
    networks:
      - observability

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./config/loki-config.yml:/etc/loki/config.yml
      - loki_data:/loki
    command: ["-config.file=/etc/loki/config.yml"]
    networks:
      - observability

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./config/promtail-config.yml:/etc/promtail/config.yml
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: ["-config.file=/etc/promtail/config.yml"]
    depends_on:
      - loki
    networks:
      - observability

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./config/grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
      - tempo
      - loki
    networks:
      - observability

volumes:
  postgres_data:
  prometheus_data:
  tempo_data:
  loki_data:
  grafana_data:

networks:
  observability:
    driver: bridge
```

**NOTE:** The app container maps port 8080 externally to port 8000 internally (Gunicorn). This keeps the student-facing port identical to the Java version.

### config/prometheus.yml

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: 'logistics-api'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['app:8000']
```

### config/tempo-config.yml

```yaml
stream_over_http_enabled: true
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        http:
          endpoint: "0.0.0.0:4318"

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

metrics_generator:
  storage:
    path: /var/tempo/metrics
```

### config/loki-config.yml

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
```

### config/promtail-config.yml

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
        filters:
          - name: label
            values: ["logging=promtail"]
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
    pipeline_stages:
      - json:
          expressions:
            level: level
            correlationId: correlationId
            service: service
      - labels:
          level:
          correlationId:
          service:
```

### config/grafana/provisioning/datasources/datasources.yml

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: true
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        filterByTraceID: true
      tracesToMetrics:
        datasourceUid: prometheus

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      derivedFields:
        - name: traceId
          datasourceUid: tempo
          matcherRegex: '"traceId":"(\w+)"'
          url: "$${__value.raw}"
```

### .dockerignore

```
__pycache__
*.pyc
*.pyo
.env
.git
.gitignore
venv/
.venv/
*.egg-info
dist/
build/
.pytest_cache/
.coverage
htmlcov/
migrations/
tests/
```

---

## 11. Data Seeder

Implement as a Flask CLI command: `flask seed`

The seeder should check if data already exists (count ports > 0) and skip if so.

### 10 Ports

| name | code | type | city | country | timezone | latitude | longitude |
|------|------|------|------|---------|----------|----------|-----------|
| Port of Seattle | USSEA | SEAPORT | Seattle | US | America/Los_Angeles | 47.6062 | -122.3321 |
| Port of Los Angeles | USLAX | SEAPORT | Los Angeles | US | America/Los_Angeles | 33.7405 | -118.2653 |
| Port of Shanghai | CNSHA | SEAPORT | Shanghai | CN | Asia/Shanghai | 31.2304 | 121.4737 |
| Port of Rotterdam | NLRTM | SEAPORT | Rotterdam | NL | Europe/Amsterdam | 51.9225 | 4.47917 |
| Port of Singapore | SGSIN | SEAPORT | Singapore | SG | Asia/Singapore | 1.2644 | 103.8220 |
| Tokyo Narita Airport | JPNRT | AIRPORT | Tokyo | JP | Asia/Tokyo | 35.7720 | 140.3929 |
| Seattle-Tacoma Airport | USSEA-AIR | AIRPORT | Seattle | US | America/Los_Angeles | 47.4502 | -122.3088 |
| Frankfurt Airport | DEFRA | AIRPORT | Frankfurt | DE | Europe/Berlin | 50.0379 | 8.5622 |
| Chicago Intermodal Terminal | USCHI-GND | GROUND_TERMINAL | Chicago | US | America/Chicago | 41.8781 | -87.6298 |
| Dallas Distribution Hub | USDAL-GND | GROUND_TERMINAL | Dallas | US | America/Chicago | 32.7767 | -96.7970 |

### 6 Carriers

| name | code | transport_modes | max_capacity_kg | current_load_kg | rating | contact_email |
|------|------|-----------------|-----------------|-----------------|--------|---------------|
| Maersk Line | MAER | OCEAN | 5000000 | 2100000 | 4.5 | ops@maersk.example.com |
| Evergreen Marine | EGRN | OCEAN | 4000000 | 1500000 | 4.2 | dispatch@evergreen.example.com |
| FedEx Freight | FDXF | AIR, GROUND | 800000 | 350000 | 4.7 | freight@fedex.example.com |
| Nippon Cargo Airlines | NCA | AIR | 600000 | 280000 | 4.3 | cargo@nca.example.com |
| XPO Logistics | XPO | GROUND | 1200000 | 700000 | 4.0 | ops@xpo.example.com |
| Hapag-Lloyd | HPLG | OCEAN | 3500000 | 2800000 | 4.1 | booking@hapag.example.com |

### 10 Routes

| origin_code | destination_code | transport_mode | estimated_transit_days | distance_km |
|-------------|-----------------|----------------|----------------------|-------------|
| USSEA | CNSHA | OCEAN | 14 | 8500 |
| CNSHA | USSEA | OCEAN | 14 | 8500 |
| USLAX | CNSHA | OCEAN | 12 | 9600 |
| USSEA | NLRTM | OCEAN | 21 | 14500 |
| NLRTM | SGSIN | OCEAN | 18 | 15000 |
| USSEA-AIR | JPNRT | AIR | 1 | 7700 |
| USSEA-AIR | DEFRA | AIR | 1 | 8200 |
| JPNRT | USSEA-AIR | AIR | 1 | 7700 |
| USCHI-GND | USDAL-GND | GROUND | 2 | 1300 |
| USDAL-GND | USCHI-GND | GROUND | 2 | 1300 |

### 5 Customers

| company_name | contact_name | contact_email | contact_phone | city | state | country | credit_limit | account_status | current_balance |
|-------------|-------------|---------------|---------------|------|-------|---------|-------------|----------------|-----------------|
| Pacific Electronics Co. | Sarah Chen | sarah.chen@pacelec.example.com | +1-206-555-0100 | Seattle | WA | US | 500000 | ACTIVE | 0 (set to 170000 after shipments created) |
| Nordic Furniture AB | Erik Lindqvist | erik@nordicfurn.example.com | +46-8-555-0200 | Stockholm | - | SE | 300000 | ACTIVE | 0 (set to 89000 after shipments created) |
| Tokyo Auto Parts Ltd | Yuki Tanaka | ytanaka@tokyoauto.example.com | +81-3-555-0300 | Tokyo | - | JP | 750000 | ACTIVE | 0 |
| Rhine Chemical GmbH | Hans Mueller | mueller@rhinechem.example.com | +49-69-555-0400 | Frankfurt | - | DE | 1000000 | ACTIVE | 0 |
| Suspended Trading Co | Bob Inactive | bob@suspended.example.com | +1-555-0500 | Portland | OR | US | 100000 | SUSPENDED | 95000 |

### 3 Shipments (created during seeding)

**Shipment 1: EXP-2026-00001**
- Customer: Pacific Electronics Co.
- Route: USSEA -> CNSHA (OCEAN)
- Status: IN_TRANSIT
- Carrier: Maersk Line
- Priority: STANDARD
- Weight: 12500 kg, Volume: 55 m3
- Declared Value: $125,000
- Estimated Departure: 2026-06-01T08:00:00
- Actual Departure: 2026-06-02T06:00:00
- Estimated Arrival: 2026-06-15T08:00:00
- 3 tracking events:
  - BOOKED at "Seattle Office" by "booking-agent" at 2026-06-01T09:00:00
  - PICKED_UP at "Customer Warehouse, Seattle" by "driver-12" at 2026-06-02T06:00:00
  - IN_TRANSIT at "Port of Seattle, Terminal 5" by "terminal-ops" at 2026-06-02T14:00:00

**Shipment 2: EXP-2026-00002**
- Customer: Nordic Furniture AB
- Route: USSEA -> NLRTM (OCEAN)
- Status: BOOKED
- Carrier: None (not yet assigned)
- Priority: EXPRESS
- Weight: 8200 kg, Volume: 120 m3
- Declared Value: $89,000
- Estimated Departure: 2026-06-10T08:00:00
- Estimated Arrival: 2026-07-01T08:00:00

**Shipment 3: EXP-2026-00003**
- Customer: Pacific Electronics Co.
- Route: USSEA -> CNSHA (OCEAN)
- Status: DRAFT
- Carrier: None
- Priority: STANDARD
- Weight: 5000 kg, Volume: 30 m3
- Declared Value: $45,000
- Special Instructions: "Fragile electronics - handle with care"
- Estimated Departure: 2026-06-20T08:00:00
- Estimated Arrival: 2026-07-04T08:00:00

After seeding:
- Pacific Electronics `current_balance` = 170000 (125000 + 45000)
- Nordic Furniture `current_balance` = 89000

---

## 12. Testing

### Test Configuration (tests/conftest.py)

- Use SQLite in-memory for tests (no Docker dependency)
- Create app with TestConfig
- Provide fixtures: `app`, `client`, `db` (with create_all/drop_all per test)
- Disable OpenTelemetry tracing in tests

### What to Test

**Service tests (unit tests with mocked db):**
- `test_create_shipment_success` - happy path
- `test_create_shipment_suspended_customer` - raises CustomerAccountSuspendedException
- `test_create_shipment_credit_exceeded` - raises CreditLimitExceededException
- `test_assign_carrier_success` - happy path
- `test_assign_carrier_wrong_mode` - raises InvalidRouteException
- `test_assign_carrier_capacity_exceeded` - raises CarrierCapacityExceededException
- `test_record_tracking_event_valid_transition` - happy path
- `test_record_tracking_event_invalid_transition` - raises InvalidStateTransitionException
- `test_cancel_shipment_releases_carrier_capacity`
- `test_cancel_shipment_restores_credit`

**Route tests (integration tests with test client):**
- `test_create_customer_returns_201`
- `test_create_customer_validation_error` - missing required fields returns 400
- `test_get_shipments_returns_paginated`
- `test_get_nonexistent_shipment_returns_404`

### Test Factories (tests/factories.py)

Use `factory-boy` with `SQLAlchemyModelFactory` for Customer, Carrier, Port, Route, Shipment.

---

## 13. Getting Started Guide (GETTING_STARTED.md)

Provide a student-facing markdown document identical in structure to the Java version, with all URLs using `http://localhost:8080` (since docker-compose maps 8080 externally).

The document walks students through:
1. Exploring seed data (customers, ports, routes, carriers)
2. Checking existing shipments
3. Creating a new shipment (with example JSON)
4. Moving a shipment through its lifecycle (tracking events)
5. Assigning carriers
6. Filing customs declarations
7. Viewing analytics
8. Cancelling shipments
9. Quick reference: status flow diagram and error codes

Include deliberate failure examples:
- Using the SUSPENDED customer ID (403)
- Exceeding credit limit (422)
- Skipping status steps (409)
- Assigning wrong carrier mode (422)
- Assigning near-full carrier (422)

---

## 14. App Factory Pattern

### app/__init__.py

```python
from flask import Flask
from app.config import DevelopmentConfig, DockerConfig, TestConfig
from app.extensions import db, migrate, ma, cors
from app.error_handlers import register_error_handlers
from app.middleware import register_middleware
from app.observability import setup_logging, setup_tracing, setup_metrics

def create_app(config_name=None):
    app = Flask(__name__)

    config_map = {
        "development": DevelopmentConfig,
        "docker": DockerConfig,
        "test": TestConfig,
    }
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    cors.init_app(app)

    # Observability
    setup_logging(app)
    setup_tracing(app)
    setup_metrics(app)

    # Middleware
    register_middleware(app)

    # Error handlers
    register_error_handlers(app)

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Health endpoint
    @app.route("/health")
    def health():
        return {"status": "UP"}

    # CLI commands
    from app.seed import seed_command
    app.cli.add_command(seed_command)

    return app
```

### run.py

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

---

## 15. Key Implementation Notes

### UUID Handling

```python
import uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String

# Use a type that works for both PostgreSQL and SQLite
from sqlalchemy import TypeDecorator

class UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))
```

### Pagination Helper

```python
def paginate_query(query, page, size):
    pagination = query.paginate(page=page + 1, per_page=size, error_out=False)
    return {
        "content": pagination.items,
        "page": page,
        "size": size,
        "totalElements": pagination.total,
        "totalPages": pagination.pages,
        "last": not pagination.has_next,
    }
```

### camelCase JSON Keys

Configure Marshmallow to output camelCase:

```python
# In each schema, use data_key for camelCase:
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True

    company_name = ma.auto_field(data_key="companyName")
    contact_name = ma.auto_field(data_key="contactName")
    # ... etc
```

Or use a global `marshmallow` helper to auto-convert snake_case to camelCase using a custom `Meta` base class.

### Logging in Services

Use structured logging with correlation ID:

```python
import logging
from flask import g

logger = logging.getLogger(__name__)

def create_shipment(...):
    # ... business logic ...
    logger.info(
        "Shipment created",
        extra={
            "correlationId": getattr(g, "correlation_id", None),
            "referenceNumber": shipment.reference_number,
            "customerId": str(customer.id),
            "customerName": customer.company_name,
            "route": f"{route.origin.code} -> {route.destination.code}",
            "mode": transport_mode.value,
            "weight": str(total_weight),
            "value": str(declared_value),
        }
    )
```

---

## 16. Running the Application

### Development (local)

```bash
# Create virtualenv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up database (requires PostgreSQL running)
flask db upgrade
flask seed

# Run
python run.py
```

### Docker (production-like, same as Java version)

```bash
docker compose up -d --build
```

Wait for all services to start, then:
- API: http://localhost:8080
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

The seeder runs automatically on app startup (as part of `create_app` or as an entrypoint script).

For Docker, add an entrypoint script that runs migrations and seeding before starting gunicorn:

```bash
#!/bin/bash
flask db upgrade
flask seed
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 run:app
```

Update the Dockerfile CMD to use this entrypoint script.
