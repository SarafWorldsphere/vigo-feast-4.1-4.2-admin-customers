from sqlalchemy import Boolean, Column, Date, Numeric, String, Time
from sqlalchemy.dialects.postgresql import UUID

from module44_backend.database import Base


class CommissionRule(Base):
    __tablename__ = "vgf_commission_rules"

    rule_id = Column(
        __import__("sqlalchemy").BigInteger,
        primary_key=True,
    )

    party_type = Column(String, nullable=False)
    commission_type = Column(String, nullable=False)
    commission_rate = Column(Numeric)

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)

    status = Column(String, nullable=False)
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