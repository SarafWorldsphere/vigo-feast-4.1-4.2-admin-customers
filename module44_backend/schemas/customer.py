from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerBase(BaseModel):
    name: str
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    default_address_id: Optional[int] = None
    loyalty_points: int = 0


class CustomerCreate(CustomerBase):
    user_id: Optional[int] = None
    franchisee_id: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[EmailStr] = None
    default_address_id: Optional[int] = None
    loyalty_points: Optional[int] = None


class CustomerStatusUpdate(BaseModel):
    is_active: bool


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    user_id: Optional[int] = None
    franchisee_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: Optional[bool] = True
    is_deleted: Optional[bool] = False


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
