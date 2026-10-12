CANCELLED_ORDER_SQL = (
    "LOWER(COALESCE(o.order_status, '')) IN ('cancelled', 'canceled') "
    "OR LOWER(COALESCE(o.cancellation_status, '')) IN ('cancelled', 'canceled')"
)
