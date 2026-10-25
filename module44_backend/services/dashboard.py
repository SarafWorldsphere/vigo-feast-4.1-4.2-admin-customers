from sqlalchemy import func
from sqlalchemy.orm import Session

from module44_backend.models.customer import Customer
from module44_backend.models.delivery_partner import DeliveryPartner
from module44_backend.models.restaurant import Restaurant
from module44_backend.models.order import Order


def get_dashboard_summary(db: Session):
    total_customers = (
        db.query(func.count(Customer.customer_id))
        .filter(Customer.is_deleted.is_(False))
        .scalar()
        or 0
    )

    active_customers = (
        db.query(func.count(Customer.customer_id))
        .filter(
            Customer.is_deleted.is_(False),
            Customer.is_active.is_(True),
        )
        .scalar()
        or 0
    )

    total_restaurants = (
        db.query(func.count(Restaurant.id))
        .filter(Restaurant.is_deleted.is_(False))
        .scalar()
        or 0
    )

    active_restaurants = (
        db.query(func.count(Restaurant.id))
        .filter(
            Restaurant.is_deleted.is_(False),
            Restaurant.is_active.is_(True),
        )
        .scalar()
        or 0
    )

    total_delivery_partners = (
        db.query(func.count(DeliveryPartner.partner_id))
        .scalar()
        or 0
    )

    active_delivery_partners = (
        db.query(func.count(DeliveryPartner.partner_id))
        .filter(DeliveryPartner.status == "ACTIVE")
        .scalar()
        or 0
    )

    total_orders = (
        db.query(func.count(Order.order_id))
        .filter(Order.is_deleted.is_(False))
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

    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.is_deleted.is_(False),
            Order.order_status != "CANCELLED",
        )
        .scalar()
        or 0
    )

    return {
        "customers": {
            "total": total_customers,
            "active": active_customers,
        },
        "restaurants": {
            "total": total_restaurants,
            "active": active_restaurants,
        },
        "delivery_partners": {
            "total": total_delivery_partners,
            "active": active_delivery_partners,
        },
        "orders": {
            "total": total_orders,
            "active": active_orders,
            "delivered": delivered_orders,
            "cancelled": cancelled_orders,
        },
        "revenue": float(total_revenue),
    }