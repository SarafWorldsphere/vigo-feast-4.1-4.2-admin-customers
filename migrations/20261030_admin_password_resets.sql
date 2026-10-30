CREATE TABLE IF NOT EXISTS vgf_adm_password_resets (
    token_hash CHAR(64) PRIMARY KEY,
    account_email VARCHAR(254) NOT NULL,
    account_mobile VARCHAR(32),
    account_source VARCHAR(64) NOT NULL
        CHECK (account_source IN ('vgf_admin', 'vgf_platform_admins')),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vgf_adm_password_resets_email_created
    ON vgf_adm_password_resets (LOWER(account_email), created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vgf_adm_password_resets_created
    ON vgf_adm_password_resets (created_at);
