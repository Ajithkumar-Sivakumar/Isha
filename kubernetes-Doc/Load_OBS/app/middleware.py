import logging
import time
import uuid

from flask import g, request

logger = logging.getLogger(__name__)

SKIP_PATHS = ("/health", "/metrics")


def _trace_id():
    try:
        from opentelemetry import trace
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return None


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlationId = getattr(g, "correlation_id", None) if _has_app_context() else None
        record.service = "logistics-api"
        record.traceId = _trace_id() if _has_app_context() else None
        return True


def _has_app_context():
    try:
        from flask import has_app_context
        return has_app_context()
    except Exception:
        return False


def register_middleware(app):
    correlation_filter = CorrelationIdFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(correlation_filter)

    @app.before_request
    def before_request():
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return

        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        g.correlation_id = correlation_id
        g.request_start_time = time.time()

        logger.info(
            "Request started: method=%s, path=%s, remoteAddr=%s",
            request.method,
            request.path,
            request.remote_addr,
            extra={
                "correlationId": correlation_id,
                "service": "logistics-api",
                "traceId": _trace_id(),
            },
        )

    @app.after_request
    def after_request(response):
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return response

        correlation_id = getattr(g, "correlation_id", None)
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id

        start_time = getattr(g, "request_start_time", None)
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            log_level = logging.WARNING if duration_ms > 3000 else logging.INFO
            logger.log(
                log_level,
                "Request completed: method=%s, path=%s, status=%s, duration=%.0fms",
                request.method,
                request.path,
                response.status_code,
                duration_ms,
                extra={
                    "correlationId": correlation_id,
                    "service": "logistics-api",
                    "durationMs": round(duration_ms),
                    "traceId": _trace_id(),
                },
            )

        return response
