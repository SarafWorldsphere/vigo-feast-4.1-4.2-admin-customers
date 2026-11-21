
from math import ceil
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from module44_backend.models.payment import Payment


def get_payments(
    db: Session,
    search: str | None = None,
    status: str | None = None,
    method: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Payment).where(
        Payment.is_active.is_(True),
        Payment.is_deleted.is_(False),
    )

    # Search by payment ID, order ID, transaction reference, or gateway.
    if search and search.strip():
        search_value = search.strip()

        search_filters = [
            func.coalesce(Payment.transaction_ref, "").ilike(f"%{search_value}%"),
            func.coalesce(Payment.gateway_name, "").ilike(f"%{search_value}%"),
            func.coalesce(Payment.gateway_order_ref, "").ilike(f"%{search_value}%"),
            func.coalesce(Payment.gateway_payment_ref, "").ilike(f"%{search_value}%"),
        ]

        if search_value.isdigit():
            search_id = int(search_value)
            search_filters.append(Payment.payment_id == search_id)

        try:
            search_order_id = UUID(search_value)
        except (ValueError, AttributeError):
            search_order_id = None
        if search_order_id is not None:
            search_filters.append(Payment.order_id == search_order_id)

        query = query.where(or_(*search_filters))

    # Case-insensitive payment status filter.
    if status:
        normalized_status = status.strip().upper()
        if normalized_status == "SUCCESS":
            query = query.where(
                func.upper(Payment.payment_status).in_(["SUCCESS", "COMPLETED"])
            )
        else:
            query = query.where(
                func.upper(Payment.payment_status) == normalized_status
            )

    # Case-insensitive payment method filter.
    if method:
        query = query.where(
            func.upper(Payment.method) == method.strip().upper()
        )

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    total_pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    payments = list(
        db.scalars(
            query
            .order_by(
                Payment.created_at.desc(),
                Payment.payment_id.desc(),
            )
            .offset(offset)
            .limit(page_size)
        ).all()
    )

    # Summary counts across all active payment records.
    base_filter = (
        Payment.is_active.is_(True),
        Payment.is_deleted.is_(False),
    )

    total_count = db.scalar(
        select(func.count(Payment.payment_id)).where(*base_filter)
    ) or 0

    successful_count = db.scalar(
        select(func.count(Payment.payment_id)).where(
            *base_filter,
            func.upper(Payment.payment_status).in_(["SUCCESS", "COMPLETED"]),
        )
    ) or 0

    pending_count = db.scalar(
        select(func.count(Payment.payment_id)).where(
            *base_filter,
            func.upper(Payment.payment_status) == "PENDING",
        )
    ) or 0

    failed_count = db.scalar(
        select(func.count(Payment.payment_id)).where(
            *base_filter,
            func.upper(Payment.payment_status) == "FAILED",
        )
    ) or 0

    items = [
        {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "method": payment.method,
            "amount": float(payment.amount or 0),
            "transaction_ref": payment.transaction_ref,
            "payment_status": payment.payment_status,
            "gateway_name": payment.gateway_name,
            "gateway_order_ref": payment.gateway_order_ref,
            "gateway_payment_ref": payment.gateway_payment_ref,
            "created_at": (
                payment.created_at.isoformat()
                if payment.created_at else None
            ),
        }
        for payment in payments
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "summary": {
            "total_payments": total_count,
            "successful_payments": successful_count,
            "pending_payments": pending_count,
            "failed_payments": failed_count,
        },
    }
