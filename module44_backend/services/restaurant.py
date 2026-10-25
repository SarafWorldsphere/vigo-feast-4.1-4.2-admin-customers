from math import ceil
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.restaurant import Restaurant
from module44_backend.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def get_restaurants(
    db: Session,
    search: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Restaurant).where(
        Restaurant.is_deleted.is_(False)
    )

    if search:
        search_value = f"%{search.strip()}%"
        query = query.where(
            or_(
                Restaurant.name.ilike(search_value),
                Restaurant.phone.ilike(search_value),
                Restaurant.email.ilike(search_value),
                Restaurant.city.ilike(search_value),
                Restaurant.state.ilike(search_value),
            )
        )

    if status:
        query = query.where(
            Restaurant.status == status
        )

    if is_active is not None:
        query = query.where(
            Restaurant.is_active.is_(is_active)
        )

    count_query = select(
        func.count()
    ).select_from(query.subquery())

    total = db.scalar(count_query) or 0

    total_pages = ceil(total / page_size) if total else 0

    offset = (page - 1) * page_size

    query = (
        query
        .order_by(Restaurant.created_at.desc())
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


def get_restaurant(
    db: Session,
    restaurant_id: str,
):
    return db.scalar(
        select(Restaurant).where(
            Restaurant.id == restaurant_id,
            Restaurant.is_deleted.is_(False),
        )
    )


def create_restaurant(
    db: Session,
    data: RestaurantCreate,
):
    restaurant = Restaurant(
        owner_id=data.owner_id,
        name=data.name,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        phone=data.phone,
        email=data.email,
        logo_url=data.logo_url,
        cover_image_url=data.cover_image_url,
        status=data.status,
        is_active=data.is_active,
        is_deleted=False,
        address_line1=data.address_line1,
        address_line2=data.address_line2,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def update_restaurant(
    db: Session,
    restaurant: Restaurant,
    data: RestaurantUpdate,
):
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return restaurant
