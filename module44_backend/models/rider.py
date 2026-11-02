from sqlalchemy import BigInteger, Boolean, Column, Date, String, Time
from sqlalchemy.dialects.postgresql import UUID

from module44_backend.database import Base
from module44_backend.config import settings


class Rider(Base):
    __tablename__ = f"{settings.db_table_prefix}riders"
    __table_args__ = {"schema": settings.db_schema}

    rider_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    vehicle_type = Column(String(50))
    status = Column(String(30), nullable=False, default="AVAILABLE")
    current_latitude = Column(String)
    current_longitude = Column(String)
    franchisee_id = Column(UUID(as_uuid=True))

    added_by = Column(String(255))
    added_date = Column(Date)
    added_time = Column(Time)
    added_ip = Column(String)

    last_updated_by = Column(String(255))
    last_updated_date = Column(Date)
    last_updated_time = Column(Time)
    last_updated_ip = Column(String)

    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)