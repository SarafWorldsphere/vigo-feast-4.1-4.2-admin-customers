from sqlalchemy import Boolean, Column, DateTime, Date, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID

from module44_backend.database import Base


class RefStatus(Base):
    __tablename__ = "vgf_ref_status"

    id = Column(UUID(as_uuid=True), primary_key=True)

    status_code = Column(String, nullable=False)
    status_name = Column(String, nullable=False)
    description = Column(Text)

    is_active = Column(Boolean, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    added_by = Column(String)
    added_date = Column(Date)
    added_time = Column(Time)
    added_ip = Column(String)

    last_updated_by = Column(String)
    last_updated_date = Column(Date)
    last_updated_time = Column(Time)
    last_updated_ip = Column(String)

    is_deleted = Column(Boolean)