CREATE TABLE IF NOT EXISTS vgf_delivery_operations_settings (
    setting_id INTEGER PRIMARY KEY CHECK (setting_id = 1),
    dispatch_mode VARCHAR(20) NOT NULL
        CHECK (dispatch_mode IN ('RIDER_POOL', 'AUTO_ASSIGN')),
    max_active_orders INTEGER NOT NULL
        CHECK (max_active_orders >= 1),
    updated_by VARCHAR(255),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vgf_delivery_rider_payouts (
    payout_id BIGSERIAL PRIMARY KEY,
    rider_id BIGINT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL CHECK (period_end >= period_start),
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'PAID')),
    reference VARCHAR(255),
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_by VARCHAR(255),
    paid_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_vgf_delivery_rider_payouts_created
    ON vgf_delivery_rider_payouts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vgf_delivery_rider_payouts_rider
    ON vgf_delivery_rider_payouts (rider_id, created_at DESC);

CREATE TABLE IF NOT EXISTS vgf_delivery_support_tickets (
    ticket_id BIGSERIAL PRIMARY KEY,
    rider_id BIGINT,
    order_id BIGINT,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL
        CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')),
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vgf_delivery_tickets_status_created
    ON vgf_delivery_support_tickets (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vgf_delivery_tickets_rider
    ON vgf_delivery_support_tickets (rider_id, created_at DESC);
