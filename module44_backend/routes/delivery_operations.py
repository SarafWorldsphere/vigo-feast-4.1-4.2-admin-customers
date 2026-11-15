from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import admin_actor, require_admin_auth
from module44_backend.database import get_db
from module44_backend.schemas.delivery_operations import (
    DispatchSettingsUpdate,
    ReassignOrderRequest,
    RiderPayoutCreate,
    RiderPayoutResponse,
    SupportTicketCreate,
    SupportTicketStatusUpdate,
)
from module44_backend.services import delivery_operations as service

router = APIRouter(
    prefix="/api/admin/delivery-operations",
    tags=["Delivery Operations"],
    dependencies=[Depends(require_admin_auth)],
)


@router.get("/settings")
def read_dispatch_settings(db: Session = Depends(get_db)):
    return service.get_dispatch_settings(db)


@router.put("/settings")
def save_dispatch_settings(
    data: DispatchSettingsUpdate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    return service.update_dispatch_settings(db, data, admin_actor(current_admin))


@router.get("/riders")
def list_dispatch_riders(db: Session = Depends(get_db)):
    return service.get_dispatch_riders(db)


@router.get("/orders")
def list_active_delivery_orders(db: Session = Depends(get_db)):
    return service.get_active_delivery_orders(db)


@router.patch("/orders/{order_id}/reassign")
def reassign_delivery_order(
    order_id: UUID,
    data: ReassignOrderRequest,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    return service.reassign_delivery_order(
        db, order_id, data.rider_id, admin_actor(current_admin)
    )


@router.get("/payouts", response_model=list[RiderPayoutResponse])
def list_rider_payouts(db: Session = Depends(get_db)):
    return service.get_rider_payouts(db)


@router.post("/payouts", response_model=RiderPayoutResponse, status_code=201)
def add_rider_payout(
    data: RiderPayoutCreate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    data = data.model_copy(update={"created_by": admin_actor(current_admin)})
    return service.create_rider_payout(db, data)


@router.patch(
    "/payouts/{payout_id}/paid",
    response_model=RiderPayoutResponse,
)
def mark_payout_paid(
    payout_id: int,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    return service.mark_rider_payout_paid(
        db, payout_id, admin_actor(current_admin)
    )


@router.get("/support-tickets")
def list_support_tickets(db: Session = Depends(get_db)):
    return service.get_support_tickets(db)


@router.post("/support-tickets", status_code=201)
def add_support_ticket(
    data: SupportTicketCreate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    data = data.model_copy(update={"created_by": admin_actor(current_admin)})
    return service.create_support_ticket(db, data)


@router.patch("/support-tickets/{ticket_id}")
def update_ticket_status(
    ticket_id: int,
    data: SupportTicketStatusUpdate,
    current_admin: dict = Depends(require_admin_auth),
    db: Session = Depends(get_db),
):
    return service.update_support_ticket_status(
        db, ticket_id, data.status, admin_actor(current_admin)
    )
