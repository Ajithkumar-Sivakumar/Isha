import logging
from datetime import datetime, timezone

from flask import jsonify, request, g
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest

from app.exceptions import ShipmentApiException

logger = logging.getLogger(__name__)


def _build_error_response(status, error_code, message, field_errors=None):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "errorCode": error_code,
        "message": message,
        "correlationId": getattr(g, "correlation_id", None),
        "path": request.path,
        "fieldErrors": field_errors or [],
    }


def register_error_handlers(app):

    @app.errorhandler(ShipmentApiException)
    def handle_api_exception(exc):
        logger.warning(
            exc.message,
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "errorCode": exc.error_code,
                "service": "logistics-api",
            },
        )
        return (
            jsonify(_build_error_response(exc.status_code, exc.error_code, exc.message)),
            exc.status_code,
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc):
        field_errors = []
        for field, messages in exc.messages.items():
            msg = messages[0] if isinstance(messages, list) else str(messages)
            field_errors.append(
                {
                    "field": field,
                    "message": msg,
                    "rejectedValue": exc.data.get(field) if exc.data else None,
                }
            )
        return (
            jsonify(
                _build_error_response(
                    400,
                    "VALIDATION_ERROR",
                    "Validation failed",
                    field_errors=field_errors,
                )
            ),
            400,
        )

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(exc):
        db_session = app.extensions.get("sqlalchemy")
        if db_session:
            db_session.session.rollback()
        return (
            jsonify(
                _build_error_response(
                    409,
                    "DATA_INTEGRITY_VIOLATION",
                    "Data integrity violation",
                )
            ),
            409,
        )

    @app.errorhandler(BadRequest)
    def handle_bad_request(exc):
        return (
            jsonify(
                _build_error_response(400, "MALFORMED_REQUEST", str(exc))
            ),
            400,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(exc):
        logger.exception(
            "Unhandled exception",
            extra={
                "correlationId": getattr(g, "correlation_id", None),
                "service": "logistics-api",
            },
        )
        return (
            jsonify(
                _build_error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
            ),
            500,
        )
