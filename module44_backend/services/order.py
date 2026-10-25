from math import ceil
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.order import Order
from module44_backend.schemas.order import OrderCreate, OrderUpdate


def get_orders(
    db: Session,
    franchisee_id: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Order).where(
        Order.is_deleted.is_(False)
    )

    if franchisee_id:
        query = query.where(
            Order.franchisee_id == franchisee_id
        )

    if search:
        search_value = f"%{search.strip()}%"

        # Search supported directly by the orders table.
        query = query.where(
            or_(
                func.cast(Order.order_id, str).ilike(search_value),
                func.cast(Order.customer_id, str).ilike(search_value),
            )
        )

    if status:
        query = query.where(
            Order.order_status == status
        )

    count_query = select(
        func.count()
    ).select_from(query.subquery())

    total = db.scalar(count_query) or 0

    total_pages = ceil(total / page_size) if total else 0

    offset = (page - 1) * page_size

    query = (
        query
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    items = list(db.scalars(query).all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_order(
    db: Session,
    order_id: int,
):
    return db.scalar(
        select(Order).where(
            Order.order_id == order_id,
            Order.is_deleted.is_(False),
        )
    )


def create_order(
    db: Session,
    data: OrderCreate,
):
    order = Order(
        customer_id=data.customer_id,
        rider_id=data.rider_id,
        restaurant_id=data.restaurant_id,
        order_status=data.order_status,
        subtotal=data.subtotal,
        gst_amount=data.gst_amount,
        delivery_charge=data.delivery_charge,
        discount_amount=data.discount_amount,
        total_amount=data.total_amount,
        cancellation_status=data.cancellation_status,
        delivery_eta=data.delivery_eta,
        offer_id=data.offer_id,
        franchisee_id=data.franchisee_id,
        is_active=True,
        is_deleted=False,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def update_order(
    db: Session,
    order: Order,
    data: OrderUpdate,
):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)

    return order
