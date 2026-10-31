ALTER TABLE vgf_adm_sessions
    ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ;

UPDATE vgf_adm_sessions
SET last_activity_at = COALESCE(created_at, NOW())
WHERE last_activity_at IS NULL;

ALTER TABLE vgf_adm_sessions
    ALTER COLUMN last_activity_at SET DEFAULT NOW(),
    ALTER COLUMN last_activity_at SET NOT NULL;
