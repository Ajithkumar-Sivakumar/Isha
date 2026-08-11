from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

PHONES = [
    {"id": 1, "name": "Acme Phone X", "price": "$799", "brand": "Acme"},
    {"id": 2, "name": "Acme Phone Lite", "price": "$499", "brand": "Acme"},
    {"id": 3, "name": "Acme Phone Pro", "price": "$999", "brand": "Acme"}
]

APP_NAME = os.getenv("APP_NAME", "Phone Demo App")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Acme Mobile")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
STORAGE_FILE = "/data/inventory.txt"

HOME_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ app_name }}</title>
</head>
<body>
  <h1>{{ app_name }}</h1>
  <p>Company: {{ company }}</p>
  <p>Admin user: <strong>{{ admin_user }}</strong></p>
  <h2>Phone Catalog</h2>
  <ul>
    {% for phone in phones %}
      <li>{{ phone.name }} - {{ phone.brand }} - {{ phone.price }}</li>
    {% endfor %}
  </ul>
  <p>Use <code>/api/phones</code> for JSON data and <code>/inventory</code> for persistent storage.</p>
</body>
</html>
"""


def save_inventory():
    try:
        os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            f.write("Phone inventory stored by the demo app.\n")
            for phone in PHONES:
                f.write(f"{phone['id']}: {phone['name']} - {phone['price']}\n")
    except OSError:
        pass


@app.route("/")
def home():
    save_inventory()
    return render_template_string(
        HOME_TEMPLATE,
        app_name=APP_NAME,
        company=COMPANY_NAME,
        admin_user=ADMIN_USER,
        phones=PHONES,
    )


@app.route("/api/phones")
def phone_api():
    return jsonify({"phones": PHONES})


@app.route("/inventory")
def inventory():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/plain; charset=utf-8"}
    return "No inventory file found. The PVC may not be mounted.", 404


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
