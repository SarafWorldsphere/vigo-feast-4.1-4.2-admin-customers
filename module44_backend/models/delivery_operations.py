from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)

from module44_backend.database import Base


class DeliveryOperationsSettings(Base):
    __tablename__ = "vgf_delivery_operations_settings"
    __table_args__ = {"schema": "public"}

    setting_id = Column(Integer, primary_key=True)
    dispatch_mode = Column(String(20), nullable=False)
    max_active_orders = Column(Integer, nullable=False)
    updated_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class RiderPayout(Base):
    __tablename__ = "vgf_delivery_rider_payouts"
    __table_args__ = {"schema": "public"}

    payout_id = Column(BigInteger, primary_key=True, autoincrement=True)
    rider_id = Column(BigInteger, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    reference = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    paid_by = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)


class DeliverySupportTicket(Base):
    __tablename__ = "vgf_delivery_support_tickets"
    __table_args__ = {"schema": "public"}

    ticket_id = Column(BigInteger, primary_key=True, autoincrement=True)
    rider_id = Column(BigInteger, nullable=True)
    order_id = Column(Uuid(as_uuid=True), nullable=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)
