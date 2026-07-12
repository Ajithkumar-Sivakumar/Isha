"""Flask application entrypoint for the containerized Python service."""

import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    """Return the home page response used to validate the service."""
    return "Hello from EKS"


@app.route("/health")
def health():
    """Return the health response used by Kubernetes probes."""
    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
