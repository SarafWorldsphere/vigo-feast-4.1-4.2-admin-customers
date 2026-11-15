from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from module44_backend.models.delivery_operations import (
    DeliveryOperationsSettings,
    DeliverySupportTicket,
    RiderPayout,
)
from module44_backend.models.delivery_partner import (
    DeliveryPartner,
    DeliveryPartnerAssignment,
)
from module44_backend.models.order import Order
from module44_backend.models.rider import Rider
from module44_backend.schemas.delivery_operations import (
    DispatchSettingsUpdate,
    RiderPayoutCreate,
    SupportTicketCreate,
)

ACTIVE_ORDER_STATUSES = (
    "PLACED",
    "CONFIRMED",
    "PREPARING",
    "READY_FOR_PICKUP",
    "OUT_FOR_DELIVERY",
)


def _settings(
    db: Session,
    for_update: bool = False,
) -> DeliveryOperationsSettings:
    settings = db.get(
        DeliveryOperationsSettings,
        1,
        with_for_update=for_update,
    )
    if settings is None:
        raise HTTPException(
            status_code=503,
            detail="Delivery operations migration has not been applied.",
        )
    return settings


def get_dispatch_settings(db: Session) -> dict:
    settings = db.get(DeliveryOperationsSettings, 1)
    if settings is None:
        return {
            "configured": False,
            "dispatch_mode": None,
            "max_active_orders": None,
            "updated_by": None,
            "updated_at": None,
        }
    return {
        "configured": True,
        "dispatch_mode": settings.dispatch_mode,
        "max_active_orders": settings.max_active_orders,
        "updated_by": settings.updated_by,
        "updated_at": settings.updated_at,
    }


def update_dispatch_settings(
    db: Session,
    data: DispatchSettingsUpdate,
    updated_by: str,
) -> dict:
    now = datetime.now(timezone.utc)
    statement = insert(DeliveryOperationsSettings).values(
        setting_id=1,
        dispatch_mode=data.dispatch_mode,
        max_active_orders=data.max_active_orders,
        updated_by=updated_by,
        updated_at=now,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[DeliveryOperationsSettings.setting_id],
        set_={
            "dispatch_mode": data.dispatch_mode,
            "max_active_orders": data.max_active_orders,
            "updated_by": updated_by,
            "updated_at": now,
        },
    )
    db.execute(statement)
    db.commit()
    return get_dispatch_settings(db)


def get_dispatch_riders(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            DeliveryPartner.rider_id,
            DeliveryPartner.full_name,
            DeliveryPartner.status,
            DeliveryPartner.verification_status,
        )
        .join(Rider, Rider.rider_id == DeliveryPartner.rider_id)
        .where(
            DeliveryPartner.rider_id.is_not(None),
            DeliveryPartner.status == "ACTIVE",
            DeliveryPartner.verification_status == "VERIFIED",
            Rider.is_active.is_(True),
            or_(Rider.is_deleted.is_(False), Rider.is_deleted.is_(None)),
        )
        .order_by(DeliveryPartner.full_name.asc())
    ).all()
    return [
        {
            "rider_id": rider_id,
            "full_name": full_name,
            "status": status,
            "verification_status": verification_status,
        }
        for rider_id, full_name, status, verification_status in rows
    ]


def assign_order_to_rider(
    db: Session,
    order: Order,
    rider_id: int | None,
    assigned_by: str,
) -> None:
    if order.rider_id == rider_id:
        return

    rider_partner = None
    if rider_id is not None:
        rider_partner = db.scalar(
            select(DeliveryPartner)
            .join(Rider, Rider.rider_id == DeliveryPartner.rider_id)
            .where(
                DeliveryPartner.rider_id == rider_id,
                DeliveryPartner.status == "ACTIVE",
                DeliveryPartner.verification_status == "VERIFIED",
                Rider.is_active.is_(True),
                or_(Rider.is_deleted.is_(False), Rider.is_deleted.is_(None)),
            )
        )
        if rider_partner is None:
            raise HTTPException(
                status_code=400,
                detail="Choose an active, approved rider.",
            )

        settings = _settings(db, for_update=True)
        active_count = db.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.rider_id == rider_id,
                Order.order_status.in_(ACTIVE_ORDER_STATUSES),
                Order.order_id != order.order_id,
                or_(Order.is_deleted.is_(False), Order.is_deleted.is_(None)),
            )
        ) or 0
        if (
            order.order_status in ACTIVE_ORDER_STATUSES
            and active_count >= settings.max_active_orders
        ):
            raise HTTPException(
                status_code=409,
                detail="The selected rider has reached the active-order limit.",
            )

    previous_rider_id = order.rider_id
    if previous_rider_id is not None:
        previous_partner = db.scalar(
            select(DeliveryPartner).where(
                DeliveryPartner.rider_id == previous_rider_id
            )
        )
        if previous_partner is not None:
            previous_assignment = db.scalar(
                select(DeliveryPartnerAssignment)
                .where(
                    DeliveryPartnerAssignment.order_id == order.order_id,
                    DeliveryPartnerAssignment.partner_id
                    == previous_partner.partner_id,
                    or_(
                        DeliveryPartnerAssignment.assignment_status.is_(None),
                        DeliveryPartnerAssignment.assignment_status.not_in(
                            ("DELIVERED", "CANCELLED", "REASSIGNED")
                        ),
                    ),
                )
                .order_by(
                    DeliveryPartnerAssignment.assignment_id.desc()
                )
                .limit(1)
                .with_for_update()
            )
            if previous_assignment is not None:
                previous_assignment.assignment_status = "REASSIGNED"
                previous_assignment.updated_at = datetime.now(timezone.utc)

    order.rider_id = rider_id
    if rider_partner is not None:
        now = datetime.now(timezone.utc)
        db.add(
            DeliveryPartnerAssignment(
                franchisee_id=rider_partner.franchisee_id,
                partner_id=rider_partner.partner_id,
                order_id=order.order_id,
                assigned_at=now,
                assignment_status="ASSIGNED",
                created_by=assigned_by,
                created_at=now,
                updated_at=now,
            )
        )


def get_active_delivery_orders(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Order.order_id,
            Order.customer_id,
            Order.rider_id,
            Order.order_status,
            Order.delivery_charge,
            Order.total_amount,
            Order.created_at,
            DeliveryPartner.full_name,
        )
        .outerjoin(DeliveryPartner, DeliveryPartner.rider_id == Order.rider_id)
        .where(
            Order.order_status.in_(ACTIVE_ORDER_STATUSES),
            or_(Order.is_deleted.is_(False), Order.is_deleted.is_(None)),
        )
        .order_by(Order.created_at.asc())
        .limit(100)
    ).all()
    return [
        {
            "order_id": order_id,
            "customer_id": customer_id,
            "rider_id": rider_id,
            "order_status": order_status,
            "delivery_charge": delivery_charge,
            "total_amount": total_amount,
            "created_at": created_at,
            "rider_name": rider_name,
        }
        for (
            order_id,
            customer_id,
            rider_id,
            order_status,
            delivery_charge,
            total_amount,
            created_at,
            rider_name,
        ) in rows
    ]


def reassign_delivery_order(
    db: Session,
    order_id: int,
    rider_id: int,
    assigned_by: str,
) -> dict:
    order = db.scalar(
        select(Order)
        .where(
            Order.order_id == order_id,
            Order.order_status.in_(ACTIVE_ORDER_STATUSES),
            or_(Order.is_deleted.is_(False), Order.is_deleted.is_(None)),
        )
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Active order not found.")

    previous_rider_id = order.rider_id
    assign_order_to_rider(db, order, rider_id, assigned_by)
    db.commit()
    return {
        "order_id": order_id,
        "previous_rider_id": previous_rider_id,
        "rider_id": rider_id,
        "rider_name": db.scalar(
            select(DeliveryPartner.full_name).where(
                DeliveryPartner.rider_id == rider_id
            )
        ),
    }


def get_rider_payouts(db: Session) -> list[dict]:
    rows = db.execute(
        select(RiderPayout, DeliveryPartner.full_name)
        .outerjoin(
            DeliveryPartner,
            DeliveryPartner.rider_id == RiderPayout.rider_id,
        )
        .order_by(RiderPayout.created_at.desc(), RiderPayout.payout_id.desc())
        .limit(200)
    ).all()
    return [
        {
            "payout_id": payout.payout_id,
            "rider_id": payout.rider_id,
            "rider_name": rider_name,
            "amount": payout.amount,
            "period_start": payout.period_start,
            "period_end": payout.period_end,
            "status": payout.status,
            "reference": payout.reference,
            "created_at": payout.created_at,
            "paid_by": payout.paid_by,
            "paid_at": payout.paid_at,
        }
        for payout, rider_name in rows
    ]


def create_rider_payout(db: Session, data: RiderPayoutCreate) -> RiderPayout:
    if data.period_end < data.period_start:
        raise HTTPException(
            status_code=422,
            detail="Payout period end must be on or after its start.",
        )
    rider_exists = db.scalar(
        select(Rider.rider_id).where(
            Rider.rider_id == data.rider_id,
            or_(Rider.is_deleted.is_(False), Rider.is_deleted.is_(None)),
        )
    )
    if rider_exists is None:
        raise HTTPException(status_code=404, detail="Rider not found.")

    payout = RiderPayout(
        rider_id=data.rider_id,
        amount=data.amount,
        period_start=data.period_start,
        period_end=data.period_end,
        status="PENDING",
        reference=data.reference,
        created_by=data.created_by,
        created_at=datetime.now(timezone.utc),
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


def mark_rider_payout_paid(
    db: Session,
    payout_id: int,
    paid_by: str | None,
) -> RiderPayout:
    payout = db.get(RiderPayout, payout_id, with_for_update=True)
    if payout is None:
        raise HTTPException(status_code=404, detail="Payout not found.")
    if payout.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Only pending payouts can be marked paid.",
        )
    payout.status = "PAID"
    payout.paid_by = paid_by
    payout.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(payout)
    return payout


def get_support_tickets(db: Session) -> list[dict]:
    rows = db.execute(
        select(DeliverySupportTicket, DeliveryPartner.full_name)
        .outerjoin(
            DeliveryPartner,
            DeliveryPartner.rider_id == DeliverySupportTicket.rider_id,
        )
        .order_by(
            DeliverySupportTicket.created_at.desc(),
            DeliverySupportTicket.ticket_id.desc(),
        )
        .limit(200)
    ).all()
    return [
        {
            "ticket_id": ticket.ticket_id,
            "rider_id": ticket.rider_id,
            "rider_name": rider_name,
            "order_id": ticket.order_id,
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_by": ticket.created_by,
            "created_at": ticket.created_at,
            "updated_by": ticket.updated_by,
            "updated_at": ticket.updated_at,
        }
        for ticket, rider_name in rows
    ]


def create_support_ticket(
    db: Session,
    data: SupportTicketCreate,
) -> DeliverySupportTicket:
    if data.rider_id is not None:
        rider_exists = db.scalar(
            select(Rider.rider_id).where(Rider.rider_id == data.rider_id)
        )
        if rider_exists is None:
            raise HTTPException(status_code=404, detail="Rider not found.")
    if data.order_id is not None:
        order_exists = db.scalar(
            select(Order.order_id).where(Order.order_id == data.order_id)
        )
        if order_exists is None:
            raise HTTPException(status_code=404, detail="Order not found.")
    now = datetime.now(timezone.utc)
    ticket = DeliverySupportTicket(
        rider_id=data.rider_id,
        order_id=data.order_id,
        subject=data.subject.strip(),
        description=data.description.strip(),
        priority=data.priority,
        status="OPEN",
        created_by=data.created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_support_ticket_status(
    db: Session,
    ticket_id: int,
    status: str,
    updated_by: str | None,
) -> DeliverySupportTicket:
    ticket = db.get(DeliverySupportTicket, ticket_id, with_for_update=True)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Support ticket not found.")
    ticket.status = status
    ticket.updated_by = updated_by
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket
