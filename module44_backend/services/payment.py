
from math import ceil

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

    # Search by Payment ID or Order ID.
    if search and search.strip():
        search_value = search.strip()

        if search_value.isdigit():
            search_id = int(search_value)
            query = query.where(
                or_(
                    Payment.payment_id == search_id,
                    Payment.order_id == search_id,
                )
            )
        else:
            query = query.where(False)

    # Case-insensitive payment status filter.
    if status:
        query = query.where(
            func.upper(Payment.payment_status) == status.strip().upper()
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
