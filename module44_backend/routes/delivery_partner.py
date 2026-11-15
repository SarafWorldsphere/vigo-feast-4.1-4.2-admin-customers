from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from sqlalchemy import or_, select
from module44_backend.models.franchisee import Franchisee

from app.dependencies import admin_actor, require_admin_auth
from module44_backend.database import get_db
from module44_backend.models.delivery_partner import DeliveryPartner
from module44_backend.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerDocumentResponse,
    DeliveryPartnerHistoryResponse,
    DeliveryPartnerResponse,
    DeliveryPartnerListResponse,
    DeliveryPartnerStatusUpdate,
    DeliveryPartnerUpdate,
    DeliveryPartnerVerificationUpdate,
)
from module44_backend.services import delivery_partner as service


router = APIRouter(
    prefix="/api/admin/delivery-partners",
    tags=["Delivery Partners"],
    dependencies=[Depends(require_admin_auth)],
)


@router.get("", response_model=DeliveryPartnerListResponse)
def list_delivery_partners(
    franchisee_id: Optional[UUID] = None,
    rider_id: Optional[int] = None,
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    verification_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return service.get_delivery_partners(
        db=db,
        franchisee_id=franchisee_id,
        rider_id=rider_id,
        search=search,
        status=status_filter,
        verification_status=verification_status,
        page=page,
        page_size=page_size,
    )

@router.get("/franchisee-options")
def get_franchisee_options(
    db: Session = Depends(get_db),
):
    query = (
        select(Franchisee)
        .where(
            Franchisee.is_active.is_(True),
            or_(
                Franchisee.is_deleted.is_(False),
                Franchisee.is_deleted.is_(None),
            ),
        )
        .order_by(Franchisee.franchisee_name.asc())
    )

    franchisees = db.execute(query).scalars().all()

    return [
        {
            "id": str(franchisee.id),
            "name": franchisee.franchisee_name,
        }
        for franchisee in franchisees
    ]


@router.get("/rider-options")
def get_rider_options(
    franchisee_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
):
    query = (
        select(DeliveryPartner.rider_id)
        .where(DeliveryPartner.rider_id.is_not(None))
    )

    if franchisee_id:
        query = query.where(
            DeliveryPartner.franchisee_id == franchisee_id
        )

    query = query.order_by(DeliveryPartner.rider_id.asc())

    rider_ids = db.execute(query).scalars().all()

    return [{"rider_id": rider_id} for rider_id in rider_ids]

@router.get("/{partner_id}", response_model=DeliveryPartnerResponse)
def get_delivery_partner(
    partner_id: int,
    franchisee_id: UUID,
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return partner

@router.post(
    "",
    response_model=DeliveryPartnerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery_partner(
    data: DeliveryPartnerCreate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    data = data.model_copy(update={"created_by": admin_actor(current_admin)})
    return service.create_delivery_partner(
        db=db,
        data=data,
    )


@router.put(
    "/{partner_id}",
    response_model=DeliveryPartnerResponse,
)
def update_delivery_partner(
    partner_id: int,
    franchisee_id: UUID,
    data: DeliveryPartnerUpdate,
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return service.update_delivery_partner(
        db=db,
        partner=partner,
        data=data,
    )


@router.patch(
    "/{partner_id}/status",
    response_model=DeliveryPartnerResponse,
)
def update_delivery_partner_status(
    partner_id: int,
    franchisee_id: UUID,
    data: DeliveryPartnerStatusUpdate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return service.update_delivery_partner_status(
        db=db,
        partner=partner,
        data=data.model_copy(update={"changed_by": admin_actor(current_admin)}),
    )


@router.patch(
    "/{partner_id}/verification",
    response_model=DeliveryPartnerResponse,
)
def update_delivery_partner_verification(
    partner_id: int,
    franchisee_id: UUID,
    data: DeliveryPartnerVerificationUpdate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return service.update_delivery_partner_verification(
        db=db,
        partner=partner,
        data=data.model_copy(update={"verified_by": admin_actor(current_admin)}),
    )


@router.patch("/{partner_id}/approve", response_model=DeliveryPartnerResponse)
def approve_delivery_partner(
    partner_id: int,
    franchisee_id: UUID,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )
    return service.approve_delivery_partner(db, partner, admin_actor(current_admin))


@router.get(
    "/{partner_id}/documents",
    response_model=list[DeliveryPartnerDocumentResponse],
)
def get_delivery_partner_documents(
    partner_id: int,
    franchisee_id: UUID,
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return service.get_delivery_partner_documents(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )


@router.get(
    "/{partner_id}/history",
    response_model=list[DeliveryPartnerHistoryResponse],
)
def get_delivery_partner_history(
    partner_id: int,
    franchisee_id: UUID,
    db: Session = Depends(get_db),
):
    partner = service.get_delivery_partner(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )

    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner not found",
        )

    return service.get_delivery_partner_history(
        db=db,
        franchisee_id=franchisee_id,
        partner_id=partner_id,
    )