from math import ceil
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.customer import Customer
from module44_backend.schemas.customer import (
    CustomerCreate,
    CustomerStatusUpdate,
    CustomerUpdate,
)


def get_customers(
    db: Session,
    franchisee_id: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Customer).where(
        Customer.is_deleted.is_(False)
    )

    if franchisee_id:
        query = query.where(
            Customer.franchisee_id == franchisee_id
        )

    if search:
        search_value = f"%{search.strip()}%"
        query = query.where(
            or_(
                Customer.name.ilike(search_value),
                Customer.mobile.ilike(search_value),
                Customer.email.ilike(search_value),
            )
        )

    if is_active is not None:
        query = query.where(
            Customer.is_active.is_(is_active)
        )

    count_query = select(
        func.count()
    ).select_from(query.subquery())

    total = db.scalar(count_query) or 0

    total_pages = ceil(total / page_size) if total else 0

    offset = (page - 1) * page_size

    query = (
        query
        .order_by(Customer.customer_id.desc())
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


def get_customer(
    db: Session,
    customer_id: int,
):
    return db.scalar(
        select(Customer).where(
            Customer.customer_id == customer_id,
            Customer.is_deleted.is_(False),
        )
    )


def create_customer(
    db: Session,
    data: CustomerCreate,
):
    customer = Customer(
        name=data.name,
        mobile=data.mobile,
        email=data.email,
        default_address_id=data.default_address_id,
        loyalty_points=data.loyalty_points,
        user_id=data.user_id,
        franchisee_id=data.franchisee_id,
        is_active=True,
        is_deleted=False,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def update_customer(
    db: Session,
    customer: Customer,
    data: CustomerUpdate,
):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


def update_customer_status(
    db: Session,
    customer: Customer,
    data: CustomerStatusUpdate,
):
    customer.is_active = data.is_active

    db.commit()
    db.refresh(customer)

    return customer
