from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module44_backend.database import get_db
from module44_backend.schemas.order import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from module44_backend.services.order import (
    create_order,
    get_order,
    get_orders,
    update_order,
)

router = APIRouter(
    prefix="/api/admin/orders",
    tags=["Orders"],
)


@router.get("", response_model=OrderListResponse)
def list_orders(
    franchisee_id: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_orders(
        db=db,
        franchisee_id=franchisee_id,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


@router.post("", response_model=OrderResponse, status_code=201)
def create_order_record(
    data: OrderCreate,
    db: Session = Depends(get_db),
):
    return create_order(db, data)


@router.put("/{order_id}", response_model=OrderResponse)
def update_order_record(
    order_id: int,
    data: OrderUpdate,
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return update_order(db, order, data)
