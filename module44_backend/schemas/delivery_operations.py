from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DispatchSettingsUpdate(BaseModel):
    dispatch_mode: Literal["RIDER_POOL", "AUTO_ASSIGN"]
    max_active_orders: int = Field(ge=1)


class ReassignOrderRequest(BaseModel):
    rider_id: int = Field(gt=0)


class RiderPayoutCreate(BaseModel):
    rider_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    period_start: date
    period_end: date
    reference: str | None = Field(default=None, max_length=255)
    created_by: str | None = None


class RiderPayoutResponse(BaseModel):
    payout_id: int
    rider_id: int
    rider_name: str | None = None
    amount: Decimal
    period_start: date
    period_end: date
    status: str
    reference: str | None = None
    created_at: datetime
    paid_by: str | None = None
    paid_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SupportTicketCreate(BaseModel):
    rider_id: int | None = Field(default=None, gt=0)
    order_id: UUID | None = None
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"
    created_by: str | None = None


class SupportTicketStatusUpdate(BaseModel):
    status: Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
    updated_by: str | None = None
