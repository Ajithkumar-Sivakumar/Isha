from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    # Root endpoint used to verify the app is reachable
    return "Hello from EKS"


@app.route("/health")
def health():
    # Liveness / readiness probe target used by Kubernetes probes
    return "OK"


if __name__ == "__main__":
    # Local dev server (not used in production container when running under gunicorn)
    app.run(host="0.0.0.0", port=8080)
