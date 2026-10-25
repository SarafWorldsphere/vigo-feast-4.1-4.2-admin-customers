from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column

from module44_backend.config import settings
from module44_backend.database import Base


class DeliveryPartner(Base):
    __tablename__ = f"{settings.db_table_prefix}delivery_partners"
    __table_args__ = {"schema": settings.db_schema}

    franchisee_id = mapped_column(UUID(as_uuid=True))
    partner_id = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    full_name = mapped_column(String(200))
    mobile_number = mapped_column(String(20))
    email = mapped_column(String(255))
    vehicle_type = mapped_column(String(100))
    vehicle_number = mapped_column(String(100))
    city = mapped_column(String(100))
    service_area = mapped_column(Text)
    status = mapped_column(String(50))
    verification_status = mapped_column(String(50))

    created_by = mapped_column(String(255))
    created_at = mapped_column(DateTime(timezone=True))

    updated_by = mapped_column(String(255))
    updated_at = mapped_column(DateTime(timezone=True))


class DeliveryPartnerDocument(Base):
    __tablename__ = f"{settings.db_table_prefix}delivery_partner_documents"
    __table_args__ = {"schema": settings.db_schema}

    franchisee_id = mapped_column(UUID(as_uuid=True))
    document_id = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    partner_id = mapped_column(BigInteger)
    document_type = mapped_column(String(100))
    document_number = mapped_column(String(100))
    file_url = mapped_column(Text)

    verification_status = mapped_column(String(50))
    verified_by = mapped_column(String(255))
    verified_at = mapped_column(DateTime(timezone=True))

    created_by = mapped_column(String(255))
    created_at = mapped_column(DateTime(timezone=True))

    updated_by = mapped_column(String(255))
    updated_at = mapped_column(DateTime(timezone=True))


class DeliveryPartnerStatusLog(Base):
    __tablename__ = f"{settings.db_table_prefix}delivery_partner_status_log"
    __table_args__ = {"schema": settings.db_schema}

    franchisee_id = mapped_column(UUID(as_uuid=True))
    log_id = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    partner_id = mapped_column(BigInteger)
    old_status = mapped_column(String(50))
    new_status = mapped_column(String(50))
    reason = mapped_column(Text)

    changed_by = mapped_column(String(255))
    changed_at = mapped_column(DateTime(timezone=True))


class DeliveryPartnerAssignment(Base):
    __tablename__ = f"{settings.db_table_prefix}delivery_partner_assignments"
    __table_args__ = {"schema": settings.db_schema}

    franchisee_id = mapped_column(UUID(as_uuid=True))
    assignment_id = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    partner_id = mapped_column(BigInteger)
    order_id = mapped_column(BigInteger)

    ordered_at = mapped_column(DateTime(timezone=True))
    approved_at = mapped_column(DateTime(timezone=True))
    assigned_at = mapped_column(DateTime(timezone=True))
    accepted_at = mapped_column(DateTime(timezone=True))
    picked_up_at = mapped_column(DateTime(timezone=True))
    delivered_at = mapped_column(DateTime(timezone=True))

    total_delivery_time = mapped_column(Integer)
    assignment_status = mapped_column(String(50))

    created_by = mapped_column(String(255))
    created_at = mapped_column(DateTime(timezone=True))

    updated_by = mapped_column(String(255))
    updated_at = mapped_column(DateTime(timezone=True))