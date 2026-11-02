from math import ceil
from re import search
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.order import Order
from module44_backend.schemas.order import OrderCreate, OrderUpdate

from module44_backend.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerAssignment,
)


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

    # Search by Order ID or Customer ID only when provided.
    if search and search.strip():
        search_value = search.strip()

        if search_value.isdigit():
            search_id = int(search_value)

            query = query.where(
                or_(
                    Order.order_id == search_id,
                    Order.customer_id == search_id
                )
            )
        else:
            query = query.where(False)

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

    # Get the latest assigned delivery partner for each order.
    query = (
        query
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    items = list(db.scalars(query).all())

    order_ids = [order.order_id for order in items]

    if order_ids:
        assignment_query = (
            select(
                DeliveryPartnerAssignment.order_id,
                DeliveryPartner.full_name,
                DeliveryPartnerAssignment.assignment_id,
            )
         .join(
         DeliveryPartner,
        DeliveryPartner.partner_id
        == DeliveryPartnerAssignment.partner_id,
            )
            .where(
                DeliveryPartnerAssignment.order_id.in_(order_ids)
            )
            .order_by(
                DeliveryPartnerAssignment.order_id,
                DeliveryPartnerAssignment.assigned_at.desc().nullslast(),
                DeliveryPartnerAssignment.assignment_id.desc(),
            )
        )

        assignment_rows = db.execute(assignment_query).all()
    partner_names = {}

    for order_id, partner_name, assignment_id in assignment_rows:
        if order_id not in partner_names:
            partner_names[order_id] = partner_name

    for order in items:
        order.delivery_partner_name = partner_names.get(order.order_id)

    else:
        for order in items:
            order.delivery_partner_name = None
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
