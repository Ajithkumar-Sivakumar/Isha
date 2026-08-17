from app.routes.shipments import shipments_bp
from app.routes.customers import customers_bp
from app.routes.carriers import carriers_bp
from app.routes.ports import ports_bp
from app.routes.routes_bp import routes_bp
from app.routes.customs import customs_bp
from app.routes.analytics import analytics_bp


def register_blueprints(app):
    app.register_blueprint(shipments_bp, url_prefix="/api/v1")
    app.register_blueprint(customers_bp, url_prefix="/api/v1")
    app.register_blueprint(carriers_bp, url_prefix="/api/v1")
    app.register_blueprint(ports_bp, url_prefix="/api/v1")
    app.register_blueprint(routes_bp, url_prefix="/api/v1")
    app.register_blueprint(customs_bp, url_prefix="/api/v1")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1")
