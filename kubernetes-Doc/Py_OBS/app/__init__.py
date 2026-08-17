import os

from flask import Flask

from app.config import DevelopmentConfig, DockerConfig, TestConfig
from app.extensions import db, migrate, ma, cors


def create_app(config_name=None):
    app = Flask(__name__)

    config_map = {
        "development": DevelopmentConfig,
        "docker": DockerConfig,
        "test": TestConfig,
    }
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    cors.init_app(app)

    from app.observability import setup_logging, setup_tracing, setup_metrics

    setup_logging(app)
    setup_tracing(app)
    setup_metrics(app)

    from app.middleware import register_middleware

    register_middleware(app)

    from app.error_handlers import register_error_handlers

    register_error_handlers(app)

    from app.routes import register_blueprints

    register_blueprints(app)

    @app.route("/health")
    def health():
        return {"status": "UP"}

    from app.seed import seed_command

    app.cli.add_command(seed_command)

    return app
