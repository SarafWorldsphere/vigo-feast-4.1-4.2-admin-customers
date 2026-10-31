import math
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise RuntimeError(f"{name} must be true or false.")
    return normalized == "true"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "production").strip().lower() or "production"
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    nimbus_user_id: str = os.getenv("NIMBUS_USER_ID", "")
    nimbus_password: str = os.getenv("NIMBUS_PASSWORD", "")
    nimbus_sender_id: str = os.getenv("NIMBUS_SENDER_ID", "")
    nimbus_entity_id: str = os.getenv("NIMBUS_ENTITY_ID", "")
    nimbus_template_id: str = os.getenv("NIMBUS_TEMPLATE_ID", "")
    nimbus_user_id_hindi: str = os.getenv("NIMBUS_USER_ID_HINDI", "")
    nimbus_password_hindi: str = os.getenv("NIMBUS_PASSWORD_HINDI", "")
    nimbus_sender_id_hindi: str = os.getenv("NIMBUS_SENDER_ID_HINDI", "")
    nimbus_entity_id_hindi: str = os.getenv("NIMBUS_ENTITY_ID_HINDI", "")
    nimbus_template_id_hindi: str = os.getenv("NIMBUS_TEMPLATE_ID_HINDI", "")
    nimbus_user_id_telugu: str = os.getenv("NIMBUS_USER_ID_TELUGU", "")
    nimbus_password_telugu: str = os.getenv("NIMBUS_PASSWORD_TELUGU", "")
    nimbus_sender_id_telugu: str = os.getenv("NIMBUS_SENDER_ID_TELUGU", "")
    nimbus_entity_id_telugu: str = os.getenv("NIMBUS_ENTITY_ID_TELUGU", "")
    nimbus_template_id_telugu: str = os.getenv("NIMBUS_TEMPLATE_ID_TELUGU", "")
    admin_session_ttl_seconds: int = int(
        os.getenv("ADMIN_SESSION_TTL_SECONDS", "43200")
    )
    admin_idle_timeout_seconds: int = int(
        os.getenv("ADMIN_IDLE_TIMEOUT_SECONDS", "1800")
    )
    remember_me_ttl_seconds: int = int(
        os.getenv("REMEMBER_ME_TTL_SECONDS", "2592000")
    )
    auth_cookie_name: str = os.getenv("ADMIN_AUTH_COOKIE_NAME", "vigo_admin_session")
    auth_cookie_path: str = os.getenv("ADMIN_AUTH_COOKIE_PATH", "/")
    auth_cookie_domain: str = os.getenv("ADMIN_AUTH_COOKIE_DOMAIN", "").strip()
    auth_cookie_secure: bool = _env_bool("ADMIN_AUTH_COOKIE_SECURE", True)
    auth_cookie_samesite: str = (
        os.getenv("ADMIN_AUTH_COOKIE_SAMESITE", "strict").strip().lower()
    )
    password_reset_ttl_seconds: int = int(
        os.getenv("PASSWORD_RESET_TTL_SECONDS", "1800")
    )
    password_reset_token_bytes: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_BYTES", "32")
    )
    password_reset_min_length: int = int(
        os.getenv("PASSWORD_RESET_MIN_LENGTH", "12")
    )
    password_reset_max_length: int = int(
        os.getenv("PASSWORD_RESET_MAX_LENGTH", "72")
    )
    password_max_bytes: int = int(os.getenv("PASSWORD_MAX_BYTES", "72"))
    password_reset_rate_limit: int = int(
        os.getenv("PASSWORD_RESET_RATE_LIMIT", "3")
    )
    password_reset_rate_window_seconds: int = int(
        os.getenv("PASSWORD_RESET_RATE_WINDOW_SECONDS", "3600")
    )
    password_reset_min_response_seconds: float = float(
        os.getenv("PASSWORD_RESET_MIN_RESPONSE_SECONDS", "1.0")
    )
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    password_reset_path: str = os.getenv("PASSWORD_RESET_PATH", "/").strip()
    smtp_host: str = os.getenv("SMTP_HOST", "").strip()
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_sender: str = os.getenv("SMTP_SENDER", "").strip()
    smtp_use_ssl: bool = _env_bool("SMTP_USE_SSL", False)
    smtp_starttls: bool = _env_bool("SMTP_STARTTLS", True)
    smtp_timeout_seconds: int = int(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))
    password_reset_email_subject: str = os.getenv(
        "PASSWORD_RESET_EMAIL_SUBJECT", "Vigo Feast password reset"
    )


settings = Settings()
if not settings.jwt_secret.strip():
    raise RuntimeError(
        "JWT_SECRET is required and must not be empty. Set it in the environment or .env."
    )
if min(
    settings.admin_session_ttl_seconds,
    settings.admin_idle_timeout_seconds,
    settings.remember_me_ttl_seconds,
    settings.password_reset_ttl_seconds,
    settings.password_reset_rate_limit,
    settings.password_reset_rate_window_seconds,
    settings.smtp_timeout_seconds,
) <= 0:
    raise RuntimeError("Session, reset, and SMTP timeout settings must be positive.")
if not math.isfinite(settings.password_reset_min_response_seconds) or (
    settings.password_reset_min_response_seconds <= 0
):
    raise RuntimeError("PASSWORD_RESET_MIN_RESPONSE_SECONDS must be positive.")
if settings.password_reset_token_bytes < 32:
    raise RuntimeError("PASSWORD_RESET_TOKEN_BYTES must be at least 32.")
if settings.password_reset_min_length < 12:
    raise RuntimeError("PASSWORD_RESET_MIN_LENGTH must be at least 12.")
if settings.password_reset_max_length < settings.password_reset_min_length:
    raise RuntimeError("PASSWORD_RESET_MAX_LENGTH must not be less than the reset minimum.")
# bcrypt input is limited to 72 bytes; reject longer inputs instead of silently truncating.
if not settings.password_reset_min_length <= settings.password_max_bytes <= 72:
    raise RuntimeError("PASSWORD_MAX_BYTES must fit the reset minimum and bcrypt limit.")
if settings.auth_cookie_samesite not in {"strict", "lax"}:
    raise RuntimeError("ADMIN_AUTH_COOKIE_SAMESITE must be strict or lax.")
if not settings.auth_cookie_secure and settings.app_env != "local":
    raise RuntimeError("ADMIN_AUTH_COOKIE_SECURE may be disabled only in local mode.")
if not settings.auth_cookie_name or not settings.auth_cookie_path.startswith("/"):
    raise RuntimeError("The admin auth cookie name and absolute path are required.")
if not 1 <= settings.smtp_port <= 65535:
    raise RuntimeError("SMTP_PORT must be a valid TCP port.")
reset_path = urlsplit(settings.password_reset_path)
if settings.password_reset_path and (
    not settings.password_reset_path.startswith("/")
    or reset_path.netloc
    or reset_path.query
    or reset_path.fragment
):
    raise RuntimeError("PASSWORD_RESET_PATH must be a path without a host or query.")
if not settings.smtp_use_ssl and not settings.smtp_starttls:
    raise RuntimeError("SMTP must use SSL or STARTTLS.")
if settings.public_base_url:
    public_url = urlsplit(settings.public_base_url)
    if (
        not public_url.netloc
        or public_url.scheme not in {"http", "https"}
        or (settings.app_env != "local" and public_url.scheme != "https")
        or public_url.query
        or public_url.fragment
        or public_url.username
        or public_url.password
    ):
        raise RuntimeError(
            "PUBLIC_BASE_URL must be an absolute HTTPS URL outside local mode, without query or fragment."
        )
