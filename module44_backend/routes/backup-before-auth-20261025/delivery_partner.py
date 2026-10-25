from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from module44_backend.database import get_db
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
)


@router.get("", response_model=DeliveryPartnerListResponse)
def list_delivery_partners(
    franchisee_id: UUID,
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
        search=search,
        status=status_filter,
        verification_status=verification_status,
        page=page,
        page_size=page_size,
    )


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
    db: Session = Depends(get_db),
):
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
        data=data,
    )


@router.patch(
    "/{partner_id}/verification",
    response_model=DeliveryPartnerResponse,
)
def update_delivery_partner_verification(
    partner_id: int,
    franchisee_id: UUID,
    data: DeliveryPartnerVerificationUpdate,
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
        data=data,
    )


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