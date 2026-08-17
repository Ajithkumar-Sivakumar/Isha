import logging
import time

from flask import request

logger = logging.getLogger(__name__)

# Micrometer-style histogram buckets (matches Spring Boot http.server.requests defaults)
_HTTP_BUCKETS = (
    0.001, 0.001048576, 0.001398101, 0.001747626, 0.002, 0.002097152, 0.002795202,
    0.003, 0.003495251, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.011,
    0.012, 0.013, 0.014, 0.015, 0.016, 0.017, 0.018, 0.019, 0.02, 0.022, 0.025,
    0.027, 0.03, 0.033, 0.036, 0.039, 0.042, 0.045, 0.048, 0.05, 0.055, 0.06,
    0.065, 0.07, 0.075, 0.08, 0.085, 0.09, 0.095, 0.1, 0.11, 0.12, 0.13, 0.14,
    0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.22, 0.25, 0.27, 0.3, 0.33, 0.36, 0.39,
    0.42, 0.45, 0.48, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0,
    1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.5, 2.7, 3.0, 3.3,
    3.6, 3.9, 4.2, 4.5, 4.8, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5,
    10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 22.0, 25.0,
    27.0, 30.0,
)

_SKIP_METRIC_PATHS = ("/health", "/metrics")


def setup_logging(app):
    try:
        from pythonjsonlogger.json import JsonFormatter

        handler = logging.StreamHandler()
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger_name",
            },
        )
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
        root_logger.setLevel(logging.INFO)

        logging.getLogger("app").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    except ImportError:
        logging.basicConfig(level=logging.INFO)


def setup_tracing(app):
    if not app.config.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.sdk.resources import Resource

        resource = Resource.create({"service.name": "logistics-api"})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(
            endpoint=app.config["OTEL_EXPORTER_OTLP_ENDPOINT"]
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FlaskInstrumentor().instrument_app(app)

        _sqla_instrumented = {"done": False}

        @app.before_request
        def _instrument_sqla_once():
            if _sqla_instrumented["done"]:
                return
            _sqla_instrumented["done"] = True
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                from app.extensions import db
                SQLAlchemyInstrumentor().instrument(engine=db.engine)
            except Exception:
                pass

    except ImportError:
        app.logger.warning("OpenTelemetry packages not installed, tracing disabled")


def _request_uri():
    if request.url_rule:
        return request.url_rule.rule
    return request.path


def setup_metrics(app):
    try:
        from prometheus_client import (
            CONTENT_TYPE_LATEST,
            GC_COLLECTOR,
            PLATFORM_COLLECTOR,
            PROCESS_COLLECTOR,
            REGISTRY,
            generate_latest,
            Histogram,
        )

        # Ensure process_resident_memory_bytes is available for saturation panel
        for collector in (PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR):
            try:
                REGISTRY.register(collector)
            except ValueError:
                pass

        request_duration = Histogram(
            "http_server_requests_seconds",
            "Duration of HTTP server requests",
            ["method", "uri", "status", "exception"],
            buckets=_HTTP_BUCKETS,
        )

        @app.before_request
        def _metrics_start_timer():
            if any(request.path.startswith(p) for p in _SKIP_METRIC_PATHS):
                return
            request.environ["_metrics_start_time"] = time.perf_counter()

        @app.after_request
        def _metrics_record(response):
            if any(request.path.startswith(p) for p in _SKIP_METRIC_PATHS):
                return response

            start = request.environ.get("_metrics_start_time")
            if start is not None:
                duration = time.perf_counter() - start
                request_duration.labels(
                    method=request.method,
                    uri=_request_uri(),
                    status=str(response.status_code),
                    exception="none",
                ).observe(duration)

            return response

        @app.route("/metrics")
        def metrics():
            from flask import Response
            return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)

    except ImportError:
        app.logger.warning("prometheus-client not installed, metrics disabled")
