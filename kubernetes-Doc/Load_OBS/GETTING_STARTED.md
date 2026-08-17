# Getting Started - Logistics API

This guide walks you through using the Logistics API. By the end, you'll know every endpoint and how to observe the application using Grafana, Prometheus, Tempo, and Loki.

## Starting the Stack

```bash
docker compose up -d --build
```

Wait about 30 seconds for all services to start. The API seeds itself automatically with sample data.

| Service    | URL                          | Credentials   |
|------------|------------------------------|---------------|
| API        | http://localhost:5000         | -             |
| Grafana    | http://localhost:3000         | admin / admin |
| Prometheus | http://localhost:9090         | -             |

---

## 1. Explore the Seed Data

### List all customers

```
GET http://localhost:5000/api/v1/customers
```

You'll see 5 customers. Note the IDs -- you'll need them later. One customer ("Suspended Trading Co") has `accountStatus: SUSPENDED`.

### List all ports

```
GET http://localhost:5000/api/v1/ports
```

10 ports: seaports, airports, and ground terminals.

### List all routes

```
GET http://localhost:5000/api/v1/routes
```

10 routes connecting the ports.

### List all carriers

```
GET http://localhost:5000/api/v1/carriers
```

6 carriers with varying transport modes and capacities.

---

## 2. Check Existing Shipments

```
GET http://localhost:5000/api/v1/shipments
```

You'll see 3 pre-seeded shipments:

| Reference       | Status     | Customer                | Route           |
|-----------------|------------|-------------------------|-----------------|
| EXP-2026-00001  | IN_TRANSIT | Pacific Electronics Co. | USSEA -> CNSHA  |
| EXP-2026-00002  | BOOKED     | Nordic Furniture AB     | USSEA -> NLRTM  |
| EXP-2026-00003  | DRAFT      | Pacific Electronics Co. | USSEA -> CNSHA  |

### Get shipment details

```
GET http://localhost:5000/api/v1/shipments/{shipmentId}
```

### View tracking history

```
GET http://localhost:5000/api/v1/shipments/{shipmentId}/tracking
```

Shipment EXP-2026-00001 has 3 tracking events showing its journey from BOOKED to IN_TRANSIT.

---

## 3. Create a New Shipment

First, get a customer ID and a route ID from the list endpoints above, then:

```
POST http://localhost:5000/api/v1/shipments
Content-Type: application/json

{
  "customerId": "<CUSTOMER_UUID>",
  "routeId": "<ROUTE_UUID>",
  "transportMode": "OCEAN",
  "priority": "STANDARD",
  "estimatedDeparture": "2026-08-01T08:00:00",
  "estimatedArrival": "2026-08-15T08:00:00",
  "totalWeight": 3000,
  "totalVolume": 25,
  "declaredValue": 50000,
  "currency": "USD",
  "items": [
    {
      "description": "Industrial Sensors",
      "quantity": 200,
      "weight": 1500
    },
    {
      "description": "Control Panels",
      "quantity": 50,
      "weight": 1500
    }
  ]
}
```

The shipment starts in **DRAFT** status.

---

## 4. Move a Shipment Through Its Lifecycle

Shipments follow this status flow:

```
DRAFT -> BOOKED -> PICKED_UP -> IN_TRANSIT -> ARRIVED_AT_PORT
                                                   |
                                        +----------+----------+
                                        |                     |
                                  CUSTOMS_HOLD         OUT_FOR_DELIVERY
                                        |                     |
                                  CUSTOMS_CLEARED        DELIVERED
                                        |
                                  OUT_FOR_DELIVERY
                                        |
                                    DELIVERED
```

DRAFT and BOOKED can also transition to CANCELLED.

### Record a tracking event (advance status)

```
POST http://localhost:5000/api/v1/shipments/{shipmentId}/tracking-events
Content-Type: application/json

{
  "status": "BOOKED",
  "location": "Booking Office",
  "notes": "Booking confirmed",
  "reportedBy": "booking-agent",
  "occurredAt": "2026-08-01T09:00:00"
}
```

Repeat with `PICKED_UP`, `IN_TRANSIT`, etc. to advance the shipment.

---

## 5. Assign a Carrier

Shipments must be in **BOOKED** status to assign a carrier.

### Find available carriers

```
GET http://localhost:5000/api/v1/carriers/available?mode=OCEAN&requiredCapacity=3000
```

### Assign

```
POST http://localhost:5000/api/v1/shipments/{shipmentId}/assign-carrier
Content-Type: application/json

{
  "carrierId": "<CARRIER_UUID>"
}
```

---

## 6. File a Customs Declaration

```
POST http://localhost:5000/api/v1/shipments/{shipmentId}/customs-declaration
Content-Type: application/json

{
  "declarationType": "EXPORT",
  "totalDeclaredValue": 50000,
  "currency": "USD"
}
```

### Submit the declaration

```
POST http://localhost:5000/api/v1/customs-declarations/{declarationId}/submit
```

This simulates an external API call -- you may notice variable response times (0.2s to 10s). This is intentional for observability exercises!

### Approve or reject

```
POST http://localhost:5000/api/v1/customs-declarations/{declarationId}/approve
```

```
POST http://localhost:5000/api/v1/customs-declarations/{declarationId}/reject?reason=Missing+documentation
```

---

## 7. View Analytics

```
GET http://localhost:5000/api/v1/analytics/shipments/summary
```

Returns aggregate data: shipments by status, by mode, carrier utilization, etc.

---

## 8. Cancel a Shipment

```
DELETE http://localhost:5000/api/v1/shipments/{shipmentId}
```

Only DRAFT or BOOKED shipments can be cancelled. Cancellation automatically releases carrier capacity and restores customer credit.

---

## 9. Try Deliberate Failures

These are designed to help you practice observability. Watch the logs and traces!

### Use the suspended customer (expect 403)

Find the "Suspended Trading Co" customer ID, then try creating a shipment with it:

```
POST http://localhost:5000/api/v1/shipments
```

Response: `403 ACCOUNT_SUSPENDED`

### Exceed credit limit (expect 422)

Create a shipment with a `declaredValue` higher than the customer's remaining credit.

Response: `422 CREDIT_LIMIT_EXCEEDED`

### Skip status steps (expect 409)

Try to record a `DELIVERED` tracking event on a `DRAFT` shipment.

Response: `409 INVALID_STATE_TRANSITION`

### Assign wrong carrier mode (expect 422)

Try assigning a ground-only carrier (XPO) to an ocean shipment.

Response: `422 INVALID_ROUTE`

### Assign near-full carrier (expect 422)

Hapag-Lloyd (HPLG) is at 2,800,000 / 3,500,000 kg. Try assigning a shipment heavier than 700,000 kg.

Response: `422 CARRIER_CAPACITY_EXCEEDED`

---

## 10. Quick Reference

### Error Codes

| Code                      | HTTP | Meaning                          |
|---------------------------|------|----------------------------------|
| RESOURCE_NOT_FOUND        | 404  | Entity doesn't exist             |
| VALIDATION_ERROR          | 400  | Request failed validation        |
| MALFORMED_REQUEST         | 400  | Unparseable request body         |
| INVALID_STATE_TRANSITION  | 409  | Status change not allowed        |
| DUPLICATE_RESOURCE        | 409  | Unique constraint violation      |
| ACCOUNT_SUSPENDED         | 403  | Customer account is suspended    |
| CREDIT_LIMIT_EXCEEDED     | 422  | Declared value exceeds credit    |
| CARRIER_CAPACITY_EXCEEDED | 422  | Carrier can't handle the weight  |
| INVALID_ROUTE             | 422  | Route/mode mismatch              |
| CUSTOMS_DECLARATION_ERROR | 422  | Customs workflow error            |
| DATA_INTEGRITY_VIOLATION  | 409  | Database constraint violation    |
| INTERNAL_ERROR            | 500  | Unexpected server error          |

### Observability Endpoints

| Endpoint   | Purpose                                      |
|------------|----------------------------------------------|
| `/health`  | Health check -- returns `{"status": "UP"}`   |
| `/metrics` | Prometheus metrics (request rate, latency)   |

### Grafana Datasources (pre-configured)

- **Prometheus** -- metrics (request rate, duration histograms)
- **Tempo** -- distributed traces (see full request flow)
- **Loki** -- logs (structured JSON, filterable by correlationId, level, service)
