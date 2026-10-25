from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module44_backend.database import get_db
from module44_backend.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerStatusUpdate,
    CustomerUpdate,
)
from module44_backend.services.customer import (
    create_customer,
    get_customer,
    get_customers,
    update_customer,
    update_customer_status,
)

router = APIRouter(
    prefix="/api/admin/customers",
    tags=["Customers"],
)


@router.get("", response_model=CustomerListResponse)
def list_customers(
    franchisee_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_customers(
        db=db,
        franchisee_id=franchisee_id,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer = get_customer(db, customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer_record(
    data: CustomerCreate,
    db: Session = Depends(get_db),
):
    return create_customer(db, data)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer_record(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
):
    customer = get_customer(db, customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return update_customer(db, customer, data)


@router.patch("/{customer_id}/status", response_model=CustomerResponse)
def update_customer_status_record(
    customer_id: int,
    data: CustomerStatusUpdate,
    db: Session = Depends(get_db),
):
    customer = get_customer(db, customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return update_customer_status(db, customer, data)
