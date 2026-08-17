"""
Shared API client for exercise scripts.
Wraps the Logistics API with helper methods that discover IDs dynamically.
Works against both the Java (Spring Boot) and Python (Flask) versions.
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:5000"


class LogisticsClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or BASE_URL
        self.session = requests.Session()

    def _url(self, path):
        return f"{self.base_url}/api/v1{path}"

    def _get(self, path, params=None, headers=None):
        return self.session.get(self._url(path), params=params, headers=headers)

    def _post(self, path, json=None, headers=None):
        return self.session.post(self._url(path), json=json, headers=headers)

    def _put(self, path, json=None, headers=None):
        return self.session.put(self._url(path), json=json, headers=headers)

    def _delete(self, path, headers=None):
        return self.session.delete(self._url(path), headers=headers)

    # --- Health ---

    def health_check(self):
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except requests.ConnectionError:
            return False

    def wait_for_ready(self, timeout=60):
        """Wait until the API is responding."""
        start = time.time()
        while time.time() - start < timeout:
            if self.health_check():
                return True
            time.sleep(2)
        print("ERROR: API not reachable. Is docker compose running?", file=sys.stderr)
        sys.exit(1)

    # --- Customers ---

    def get_customers(self, page=0, size=100):
        r = self._get("/customers", params={"page": page, "size": size})
        r.raise_for_status()
        return r.json()

    def get_customer_by_name(self, name):
        """Find a customer by company name (partial match via search)."""
        r = self._get("/customers", params={"search": name, "size": 100})
        r.raise_for_status()
        data = r.json()
        for c in data.get("content", []):
            if name.lower() in c["companyName"].lower():
                return c
        return None

    def get_customer(self, customer_id):
        r = self._get(f"/customers/{customer_id}")
        r.raise_for_status()
        return r.json()

    def create_customer(self, company_name, contact_name, email, credit_limit,
                        city="Seattle", state="WA", country="US"):
        payload = {
            "companyName": company_name,
            "contactName": contact_name,
            "contactEmail": email,
            "street": "100 Main St",
            "city": city,
            "state": state,
            "country": country,
            "creditLimit": credit_limit
        }
        r = self._post("/customers", json=payload)
        return r

    def get_customer_shipments(self, customer_id, page=0, size=20):
        r = self._get(f"/customers/{customer_id}/shipments", params={"page": page, "size": size})
        return r

    # --- Carriers ---

    def get_carriers(self, mode=None, active_only=True):
        params = {"activeOnly": active_only}
        if mode:
            params["mode"] = mode
        r = self._get("/carriers", params=params)
        r.raise_for_status()
        return r.json()

    def get_carrier_by_code(self, code):
        """Find a carrier by its code (e.g. MAER, HPLG)."""
        carriers = self.get_carriers(active_only=False)
        for c in carriers:
            if c["code"] == code:
                return c
        return None

    def get_available_carriers(self, mode, required_capacity):
        r = self._get("/carriers/available", params={
            "mode": mode, "requiredCapacity": required_capacity
        })
        r.raise_for_status()
        return r.json()

    # --- Ports ---

    def get_ports(self, port_type=None, country=None):
        params = {}
        if port_type:
            params["type"] = port_type
        if country:
            params["country"] = country
        r = self._get("/ports", params=params)
        r.raise_for_status()
        return r.json()

    # --- Routes ---

    def get_routes(self, origin=None, destination=None, mode=None):
        params = {}
        if origin:
            params["origin"] = origin
        if destination:
            params["destination"] = destination
        if mode:
            params["mode"] = mode
        r = self._get("/routes", params=params)
        r.raise_for_status()
        return r.json()

    def get_route_by_codes(self, origin_code, dest_code, mode=None):
        """Find a route by origin/destination port codes."""
        routes = self.get_routes(origin=origin_code, destination=dest_code, mode=mode)
        return routes[0] if routes else None

    # --- Shipments ---

    def get_shipments(self, page=0, size=20, **filters):
        params = {"page": page, "size": size}
        params.update(filters)
        r = self._get("/shipments", params=params)
        return r

    def get_shipment(self, shipment_id):
        r = self._get(f"/shipments/{shipment_id}")
        return r

    def create_shipment(self, customer_id, route_id, transport_mode, total_weight,
                        declared_value, items, priority="STANDARD",
                        estimated_departure="2026-08-01T08:00:00",
                        estimated_arrival="2026-08-15T08:00:00",
                        special_instructions=None):
        payload = {
            "customerId": customer_id,
            "routeId": route_id,
            "transportMode": transport_mode,
            "priority": priority,
            "estimatedDeparture": estimated_departure,
            "estimatedArrival": estimated_arrival,
            "totalWeight": total_weight,
            "declaredValue": declared_value,
            "items": items
        }
        if special_instructions:
            payload["specialInstructions"] = special_instructions
        r = self._post("/shipments", json=payload)
        return r

    def assign_carrier(self, shipment_id, carrier_id):
        r = self._post(f"/shipments/{shipment_id}/assign-carrier", json={"carrierId": carrier_id})
        return r

    def cancel_shipment(self, shipment_id):
        r = self._delete(f"/shipments/{shipment_id}")
        return r

    # --- Tracking Events ---

    def create_tracking_event(self, shipment_id, status, location, reported_by,
                              occurred_at="2026-08-01T10:00:00", notes=None):
        payload = {
            "status": status,
            "location": location,
            "reportedBy": reported_by,
            "occurredAt": occurred_at
        }
        if notes:
            payload["notes"] = notes
        r = self._post(f"/shipments/{shipment_id}/tracking-events", json=payload)
        return r

    def get_tracking_history(self, shipment_id):
        r = self._get(f"/shipments/{shipment_id}/tracking")
        return r

    # --- Customs ---

    def create_customs_declaration(self, shipment_id, declaration_type="IMPORT",
                                   total_declared_value=10000, currency="USD"):
        payload = {
            "declarationType": declaration_type,
            "totalDeclaredValue": total_declared_value,
            "currency": currency
        }
        r = self._post(f"/shipments/{shipment_id}/customs-declaration", json=payload)
        return r

    def submit_customs_declaration(self, declaration_id):
        r = self._post(f"/customs-declarations/{declaration_id}/submit")
        return r

    def get_customs_declaration(self, shipment_id):
        r = self._get(f"/shipments/{shipment_id}/customs-declaration")
        return r

    # --- Analytics ---

    def get_analytics_summary(self):
        r = self._get("/analytics/shipments/summary")
        return r

    def get_carrier_performance(self):
        r = self._get("/analytics/shipments/carrier-performance")
        return r


# --- Helpers for scripts ---

def make_item(description="General Cargo", quantity=10, weight=500,
              hs_code="8471.30.01", country_of_origin="US",
              is_dangerous=False):
    return {
        "description": description,
        "quantity": quantity,
        "weight": weight,
        "hsCode": hs_code,
        "countryOfOrigin": country_of_origin,
        "isDangerous": is_dangerous,
        "temperatureControlled": False
    }


def progress(msg):
    """Print a progress message with timestamp."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
