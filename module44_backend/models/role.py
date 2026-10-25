from sqlalchemy import BigInteger, Boolean, Column, Date, String, Time
from sqlalchemy.dialects.postgresql import UUID

from module44_backend.database import Base


class Role(Base):
    __tablename__ = "vgf_roles"

    role_id = Column(BigInteger, primary_key=True)
    role_name = Column(String, nullable=False)

    franchisee_id = Column(UUID(as_uuid=True))

    added_by = Column(String)
    added_date = Column(Date)
    added_time = Column(Time)
    added_ip = Column(String)

    last_updated_by = Column(String)
    last_updated_date = Column(Date)
    last_updated_time = Column(Time)
    last_updated_ip = Column(String)

    is_active = Column(Boolean)
    is_deleted = Column(Boolean)