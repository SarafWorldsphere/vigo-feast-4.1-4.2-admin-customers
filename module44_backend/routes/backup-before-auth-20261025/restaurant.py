from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module44_backend.database import get_db
from module44_backend.schemas.restaurant import (
    RestaurantCreate,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from module44_backend.services.restaurant import (
    create_restaurant,
    get_restaurant,
    get_restaurants,
    update_restaurant,
)

router = APIRouter(
    prefix="/api/admin/restaurants",
    tags=["Restaurants"],
)


@router.get("", response_model=RestaurantListResponse)
def list_restaurants(
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_restaurants(
        db=db,
        search=search,
        status=status,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant_by_id(
    restaurant_id: str,
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return restaurant


@router.post("", response_model=RestaurantResponse, status_code=201)
def create_restaurant_record(
    data: RestaurantCreate,
    db: Session = Depends(get_db),
):
    return create_restaurant(db, data)


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant_record(
    restaurant_id: str,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return update_restaurant(db, restaurant, data)
