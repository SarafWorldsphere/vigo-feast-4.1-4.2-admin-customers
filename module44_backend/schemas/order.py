from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    delivery_charge: Optional[float] = Field(default=None, ge=0)
    restaurant_id: Optional[str] = None
    order_status: Optional[str] = None
    cancellation_status: Optional[str] = None
    delivery_eta: Optional[datetime] = None
    offer_id: Optional[int] = None

    @model_validator(mode="after")
    def reject_null_delivery_charge(self):
        if (
            "delivery_charge" in self.model_fields_set
            and self.delivery_charge is None
        ):
            raise ValueError("Delivery fee cannot be null.")
        return self


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    customer_id: Optional[int] = None
    franchisee_id: Optional[str] = None
    delivery_partner_name: Optional[str] = None
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