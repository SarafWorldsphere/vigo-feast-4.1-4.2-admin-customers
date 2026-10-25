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


class Order(Base):
    __tablename__ = "vgf_orders"
    __table_args__ = {"schema": "public"}

    order_id = Column(BigInteger, primary_key=True)
    customer_id = Column(BigInteger, nullable=False)
    rider_id = Column(BigInteger, nullable=True)
    order_status = Column(String, nullable=False)
    subtotal = Column(Numeric, nullable=False, default=0)
    gst_amount = Column(Numeric, nullable=False, default=0)
    delivery_charge = Column(Numeric, nullable=False, default=0)
    discount_amount = Column(Numeric, nullable=False, default=0)
    total_amount = Column(Numeric, nullable=False, default=0)
    cancellation_status = Column(String, nullable=True)
    delivery_eta = Column(DateTime(timezone=True), nullable=True)
    offer_id = Column(BigInteger, nullable=True)
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
    restaurant_id = Column(UUID(as_uuid=False), nullable=True)
