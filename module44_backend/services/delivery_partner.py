from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerDocument,
    DeliveryPartnerStatusLog,
)
from module44_backend.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerStatusUpdate,
    DeliveryPartnerUpdate,
    DeliveryPartnerVerificationUpdate,
)


def get_delivery_partners(
    db: Session,
    franchisee_id: UUID,
    search: str | None = None,
    status: str | None = None,
    verification_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(DeliveryPartner).where(
        DeliveryPartner.franchisee_id == franchisee_id
    )

    if search:
        search_value = f"%{search}%"

        query = query.where(
            or_(
                DeliveryPartner.full_name.ilike(search_value),
                DeliveryPartner.mobile_number.ilike(search_value),
                DeliveryPartner.email.ilike(search_value),
                DeliveryPartner.vehicle_number.ilike(search_value),
            )
        )

    if status:
        query = query.where(DeliveryPartner.status == status)

    if verification_status:
        query = query.where(
            DeliveryPartner.verification_status == verification_status
        )

    count_query = select(
        func.count()
    ).select_from(query.subquery())

    total = db.execute(count_query).scalar_one()

    query = query.order_by(DeliveryPartner.partner_id.desc())

    offset = (page - 1) * page_size

    query = query.offset(offset).limit(page_size)

    partners = db.execute(query).scalars().all()

    return {
        "items": partners,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_delivery_partner(
    db: Session,
    franchisee_id: UUID,
    partner_id: int,
):
    query = select(DeliveryPartner).where(
        DeliveryPartner.franchisee_id == franchisee_id,
        DeliveryPartner.partner_id == partner_id,
    )

    return db.execute(query).scalar_one_or_none()


def create_delivery_partner(
    db: Session,
    data: DeliveryPartnerCreate,
):
    partner = DeliveryPartner(
        franchisee_id=data.franchisee_id,
        full_name=data.full_name,
        mobile_number=data.mobile_number,
        email=data.email,
        vehicle_type=data.vehicle_type,
        vehicle_number=data.vehicle_number,
        city=data.city,
        service_area=data.service_area,
        status="PENDING",
        verification_status="PENDING",
        created_by=data.created_by,
        created_at=datetime.now(timezone.utc),
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    return partner


def update_delivery_partner(
    db: Session,
    partner: DeliveryPartner,
    data: DeliveryPartnerUpdate,
):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(partner, field, value)

    partner.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(partner)

    return partner


def update_delivery_partner_status(
    db: Session,
    partner: DeliveryPartner,
    data: DeliveryPartnerStatusUpdate,
):
    old_status = partner.status

    partner.status = data.status
    partner.updated_at = datetime.now(timezone.utc)
    partner.updated_by = data.changed_by

    status_log = DeliveryPartnerStatusLog(
        franchisee_id=partner.franchisee_id,
        partner_id=partner.partner_id,
        old_status=old_status,
        new_status=data.status,
        reason=data.reason,
        changed_by=data.changed_by,
        changed_at=datetime.now(timezone.utc),
    )

    db.add(status_log)
    db.commit()
    db.refresh(partner)

    return partner


def update_delivery_partner_verification(
    db: Session,
    partner: DeliveryPartner,
    data: DeliveryPartnerVerificationUpdate,
):
    partner.verification_status = data.verification_status
    partner.updated_by = data.verified_by
    partner.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(partner)

    return partner


def get_delivery_partner_documents(
    db: Session,
    franchisee_id: UUID,
    partner_id: int,
):
    query = select(DeliveryPartnerDocument).where(
        DeliveryPartnerDocument.franchisee_id == franchisee_id,
        DeliveryPartnerDocument.partner_id == partner_id,
    )

    return db.execute(query).scalars().all()


def get_delivery_partner_history(
    db: Session,
    franchisee_id: UUID,
    partner_id: int,
):
    query = (
        select(DeliveryPartnerStatusLog)
        .where(
            DeliveryPartnerStatusLog.franchisee_id == franchisee_id,
            DeliveryPartnerStatusLog.partner_id == partner_id,
        )
        .order_by(DeliveryPartnerStatusLog.changed_at.desc())
    )

    return db.execute(query).scalars().all()