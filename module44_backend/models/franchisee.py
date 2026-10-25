from sqlalchemy import Boolean, Column, Date, DateTime, String, Time
from sqlalchemy.dialects.postgresql import UUID

from module44_backend.database import Base


class Franchisee(Base):
    __tablename__ = "vgf_franchisees"

    id = Column(UUID(as_uuid=True), primary_key=True)
    franchisee_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    added_by = Column(String)
    added_date = Column(Date)
    added_time = Column(Time)
    added_ip = Column(String)

    last_updated_by = Column(String)
    last_updated_date = Column(Date)
    last_updated_time = Column(Time)
    last_updated_ip = Column(String)

    is_deleted = Column(Boolean)
    franchisee_id = Column(UUID(as_uuid=True))