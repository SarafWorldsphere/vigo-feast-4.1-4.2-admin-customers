from sqlalchemy import func
from sqlalchemy.orm import Session

from module44_backend.models.customer import Customer
from module44_backend.models.delivery_partner import DeliveryPartner
from module44_backend.models.restaurant import Restaurant
from module44_backend.models.order import Order


def get_reports_summary(db: Session):
    total_orders = (
        db.query(func.count(Order.order_id))
        .filter(Order.is_deleted.is_(False))
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.is_deleted.is_(False),
            Order.order_status != "CANCELLED",
        )
        .scalar()
        or 0
    )

    delivered_orders = (
        db.query(func.count(Order.order_id))
        .filter(
            Order.is_deleted.is_(False),
            Order.order_status == "DELIVERED",
        )
        .scalar()
        or 0
    )

    cancelled_orders = (
        db.query(func.count(Order.order_id))
        .filter(
            Order.is_deleted.is_(False),
            Order.order_status == "CANCELLED",
        )
        .scalar()
        or 0
    )

    active_orders = (
        db.query(func.count(Order.order_id))
        .filter(
            Order.is_deleted.is_(False),
            Order.order_status.notin_(["DELIVERED", "CANCELLED"]),
        )
        .scalar()
        or 0
    )

    customers = (
        db.query(func.count(Customer.customer_id))
        .filter(Customer.is_deleted.is_(False))
        .scalar()
        or 0
    )

    restaurants = (
        db.query(func.count(Restaurant.id))
        .filter(Restaurant.is_deleted.is_(False))
        .scalar()
        or 0
    )

    delivery_partners = (
        db.query(func.count(DeliveryPartner.partner_id))
        .scalar()
        or 0
    )

    status_rows = (
        db.query(
            Order.order_status,
            func.count(Order.order_id),
        )
        .filter(Order.is_deleted.is_(False))
        .group_by(Order.order_status)
        .order_by(func.count(Order.order_id).desc())
        .all()
    )

    order_status = [
        {
            "status": status,
            "count": count,
        }
        for status, count in status_rows
    ]

    average_order_value = (
        float(total_revenue) / total_orders
        if total_orders > 0
        else 0
    )

    return {
        "overview": {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": float(total_revenue),
            "average_order_value": float(average_order_value),
        },
        "platform": {
            "customers": customers,
            "restaurants": restaurants,
            "delivery_partners": delivery_partners,
        },
        "order_status": order_status,
    }