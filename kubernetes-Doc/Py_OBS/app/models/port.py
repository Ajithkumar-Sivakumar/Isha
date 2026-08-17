import uuid

from app.extensions import db
from app.enums import PortType
from app.models.uuid_type import UUID


class Port(db.Model):
    __tablename__ = "ports"

    id = db.Column(UUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    type = db.Column(db.Enum(PortType), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
