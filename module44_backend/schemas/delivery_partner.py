from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class DeliveryPartnerBase(BaseModel):
    franchisee_id: UUID
    full_name: str
    mobile_number: str
    email: EmailStr | None = None
    vehicle_type: str | None = None
    vehicle_number: str | None = None
    city: str | None = None
    service_area: str | None = None


class DeliveryPartnerCreate(DeliveryPartnerBase):
    created_by: str | None = None


class DeliveryPartnerUpdate(BaseModel):
    full_name: str | None = None
    mobile_number: str | None = None
    email: EmailStr | None = None
    vehicle_type: str | None = None
    vehicle_number: str | None = None
    city: str | None = None
    service_area: str | None = None
    updated_by: str | None = None


class DeliveryPartnerStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
    changed_by: str | None = None


class DeliveryPartnerVerificationUpdate(BaseModel):
    verification_status: str
    verified_by: str | None = None


class DeliveryPartnerResponse(DeliveryPartnerBase):
    partner_id: int
    status: str | None = None
    verification_status: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_by: str | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryPartnerDocumentResponse(BaseModel):
    document_id: int
    franchisee_id: UUID | None = None
    partner_id: int | None = None
    document_type: str | None = None
    document_number: str | None = None
    file_url: str | None = None
    verification_status: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryPartnerHistoryResponse(BaseModel):
    log_id: int
    franchisee_id: UUID | None = None
    partner_id: int | None = None
    old_status: str | None = None
    new_status: str | None = None
    reason: str | None = None
    changed_by: str | None = None
    changed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryPartnerListResponse(BaseModel):
    items: list[DeliveryPartnerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int