
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Numeric,
    String,
    Time,
)
from sqlalchemy.dialects.postgresql import INET, UUID

from module44_backend.database import Base


class Payment(Base):
    __tablename__ = "vgf_payments"
    __table_args__ = {"schema": "public"}

    payment_id = Column(BigInteger, primary_key=True)
    order_id = Column(BigInteger, nullable=False)
    method = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    transaction_ref = Column(String, nullable=True)
    payment_status = Column(String, nullable=False)
    gateway_name = Column(String, nullable=True)
    gateway_order_ref = Column(String, nullable=True)
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

    is_active = Column(Boolean, nullable=True)
    is_deleted = Column(Boolean, nullable=True)

    gateway_payment_ref = Column(String, nullable=True)
    demo_marker = Column(String, nullable=True)
