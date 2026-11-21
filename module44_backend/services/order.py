from datetime import datetime, timezone
from math import ceil
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.delivery_operations import DeliveryOperationsSettings
from module44_backend.models.order import Order
from module44_backend.schemas.order import OrderCreate, OrderUpdate

from module44_backend.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerAssignment,
)
from module44_backend.models.rider import Rider
from module44_backend.services.delivery_operations import assign_order_to_rider


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

        try:
            search_order_id = UUID(search_value)
        except ValueError:
            search_order_id = None

        if search_order_id is not None:
            query = query.where(
                Order.order_id == search_order_id
            )
        elif search_value.isdigit():
            query = query.where(Order.customer_id == int(search_value))
        else:
            query = query.where(False)

    if status:
        normalized_status = status.strip().upper()
        if normalized_status in {"CONFIRMED", "ACCEPTED"}:
            query = query.where(
                func.upper(Order.order_status).in_(["CONFIRMED", "ACCEPTED"])
            )
        else:
            query = query.where(
                func.upper(Order.order_status) == normalized_status
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

    partner_names = {}

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

        for order_id, partner_name, assignment_id in assignment_rows:
            if order_id not in partner_names:
                partner_names[order_id] = partner_name

    for order in items:
        order.delivery_partner_name = partner_names.get(order.order_id)


    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }



def get_order(
    db: Session,
    order_id: UUID,
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
    created_by: str,
):
    now = datetime.now(timezone.utc)
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
        created_at=now,
        updated_at=now,
        is_active=True,
        is_deleted=False,
    )

    db.add(order)
    db.flush()

    if data.rider_id is not None and order.order_status in {
        "PLACED",
        "CONFIRMED",
        "PREPARING",
        "READY_FOR_PICKUP",
        "OUT_FOR_DELIVERY",
    }:
        order.rider_id = None
        assign_order_to_rider(db, order, data.rider_id, created_by)
    elif data.rider_id is None:
        dispatch_settings = db.get(
            DeliveryOperationsSettings,
            1,
        )
        if (
            dispatch_settings is not None
            and dispatch_settings.dispatch_mode == "AUTO_ASSIGN"
        ):
            dispatch_settings = db.scalar(
                select(DeliveryOperationsSettings)
                .where(DeliveryOperationsSettings.setting_id == 1)
                .with_for_update()
            )
        if (
            dispatch_settings is not None
            and dispatch_settings.dispatch_mode == "AUTO_ASSIGN"
            and order.order_status in {
                "PLACED",
                "CONFIRMED",
                "PREPARING",
                "READY_FOR_PICKUP",
                "OUT_FOR_DELIVERY",
            }
        ):
            active_loads = (
                select(Order.rider_id, func.count().label("active_count"))
                .where(
                    Order.rider_id.is_not(None),
                    Order.order_status.in_(
                        (
                            "PLACED",
                            "CONFIRMED",
                            "PREPARING",
                            "READY_FOR_PICKUP",
                            "OUT_FOR_DELIVERY",
                        )
                    ),
                    or_(Order.is_deleted.is_(False), Order.is_deleted.is_(None)),
                )
                .group_by(Order.rider_id)
                .subquery()
            )
            candidates = db.execute(
                select(
                    DeliveryPartner,
                    func.coalesce(active_loads.c.active_count, 0).label(
                        "active_count"
                    ),
                )
                .join(Rider, Rider.rider_id == DeliveryPartner.rider_id)
                .outerjoin(
                    active_loads,
                    active_loads.c.rider_id == DeliveryPartner.rider_id,
                )
                .where(
                    DeliveryPartner.rider_id.is_not(None),
                    DeliveryPartner.status == "ACTIVE",
                    DeliveryPartner.verification_status == "VERIFIED",
                    Rider.is_active.is_(True),
                    or_(Rider.is_deleted.is_(False), Rider.is_deleted.is_(None)),
                    func.coalesce(active_loads.c.active_count, 0)
                    < dispatch_settings.max_active_orders,
                )
                .order_by(
                    func.coalesce(active_loads.c.active_count, 0),
                    DeliveryPartner.rider_id.asc(),
                )
                .limit(1)
            ).first()
            if candidates is not None:
                partner, _active_count = candidates
                assign_order_to_rider(
                    db,
                    order,
                    partner.rider_id,
                    created_by,
                )

    db.commit()
    db.refresh(order)

    return order


def update_order(
    db: Session,
    order: Order,
    data: OrderUpdate,
    updated_by: str,
):
    update_data = data.model_dump(exclude_unset=True)

    if "rider_id" in update_data:
        assign_order_to_rider(
            db,
            order,
            update_data.pop("rider_id"),
            updated_by,
        )

    for field, value in update_data.items():
        setattr(order, field, value)

    order.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)

    return order
