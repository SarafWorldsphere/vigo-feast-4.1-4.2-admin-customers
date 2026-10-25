from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Time,
)
from sqlalchemy.dialects.postgresql import INET, UUID

from module44_backend.database import Base


class Customer(Base):
    __tablename__ = "vgf_customers"
    __table_args__ = {"schema": "public"}

    customer_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=True)
    name = Column(String, nullable=False)
    mobile = Column(String, nullable=True)
    email = Column(String, nullable=True)
    default_address_id = Column(BigInteger, nullable=True)
    loyalty_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    franchisee_id = Column(UUID(as_uuid=False), nullable=True)
    added_by = Column(String, nullable=True)
    added_date = Column(Date, nullable=True)
    added_time = Column(Time, nullable=True)
    added_ip = Column(INET, nullable=True)
    last_updated_by = Column(String, nullable=True)
    last_updated_date = Column(Date, nullable=True)
    last_updated_time = Column(Time, nullable=True)
    last_updated_ip = Column(INET, nullable=True)
    is_active = Column(Boolean, nullable=True, default=True)
    is_deleted = Column(Boolean, nullable=True, default=False)
