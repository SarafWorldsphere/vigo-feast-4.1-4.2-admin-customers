from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderBase(BaseModel):
    customer_id: int
    rider_id: Optional[int] = None
    restaurant_id: Optional[str] = None
    order_status: str
    subtotal: float
    gst_amount: float
    delivery_charge: float
    discount_amount: float
    total_amount: float
    cancellation_status: Optional[str] = None
    delivery_eta: Optional[datetime] = None
    offer_id: Optional[int] = None


class OrderCreate(OrderBase):
    franchisee_id: Optional[str] = None


class OrderUpdate(BaseModel):
    rider_id: Optional[int] = None
    restaurant_id: Optional[str] = None
    order_status: Optional[str] = None
    cancellation_status: Optional[str] = None
    delivery_eta: Optional[datetime] = None
    offer_id: Optional[int] = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    franchisee_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
