import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from twilio.rest import Client

from app.config import settings
from app.db import get_db_connection


def _normalize_phone_number(phone: str | None) -> str:
    return (phone or "").strip()


def verify_password(plain_password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    candidate = stored_hash.strip()
    if candidate.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                candidate.encode("utf-8"),
            )
        except (ValueError, TypeError):
            return False

    if candidate.lower() == hashlib.sha256(plain_password.encode("utf-8")).hexdigest():
        return True

    return settings.app_env == "local" and candidate == plain_password


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def create_admin_token(admin: dict[str, Any], session_id: str | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
    admin_id = admin.get("admin_id")
    franchisee_id = admin.get("franchisee_id")
    payload = {
        "sub": admin.get("username") or admin.get("email") or admin.get("mobile_no") or admin.get("phone"),
        "role": admin.get("role") or "admin",
        "admin_id": str(admin_id) if isinstance(admin_id, uuid.UUID) else admin_id,
        "franchisee_id": str(franchisee_id) if isinstance(franchisee_id, uuid.UUID) else franchisee_id,
        "session_id": session_id,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def _fetch_default_franchisee_id(cur) -> str | None:
    cur.execute("SELECT id FROM vgf_franchisees ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    return row[0] if row else None


def find_admin_by_username(username: str) -> dict[str, Any] | None:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT admin_id, franchisee_id, full_name, email, mobile_no, username, password_hash, role, is_active
                FROM vgf_admin
                WHERE username = %s OR email = %s
                LIMIT 1
                """,
                (username, username),
            )
            row = cur.fetchone()
            if row:
                return {
                    "admin_id": row[0],
                    "franchisee_id": row[1],
                    "full_name": row[2],
                    "email": row[3],
                    "mobile_no": row[4],
                    "username": row[5],
                    "password_hash": row[6],
                    "role": row[7],
                    "is_active": row[8],
                    "source": "vgf_admin",
                }

            cur.execute(
                """
                SELECT id, email, phone, password_hash, role, is_active, franchisee_id, name
                FROM vgf_platform_admins
                WHERE email = %s OR phone = %s
                LIMIT 1
                """,
                (username, username),
            )
            row = cur.fetchone()
            if row:
                return {
                    "admin_id": row[0],
                    "franchisee_id": row[6],
                    "full_name": row[7] or row[1],
                    "email": row[1],
                    "mobile_no": row[2],
                    "username": row[1],
                    "password_hash": row[3],
                    "role": row[4],
                    "is_active": row[5],
                    "source": "vgf_platform_admins",
                }

    return None


def find_admin_by_mobile(mobile_number: str) -> dict[str, Any] | None:
    normalized = _normalize_phone_number(mobile_number)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT admin_id, franchisee_id, full_name, email, mobile_no, username, password_hash, role, is_active
                FROM vgf_admin
                WHERE mobile_no = %s
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "admin_id": row[0],
                    "franchisee_id": row[1],
                    "full_name": row[2],
                    "email": row[3],
                    "mobile_no": row[4],
                    "username": row[5],
                    "password_hash": row[6],
                    "role": row[7],
                    "is_active": row[8],
                    "source": "vgf_admin",
                }

            cur.execute(
                """
                SELECT id, email, phone, password_hash, role, is_active, franchisee_id, name
                FROM vgf_platform_admins
                WHERE phone = %s
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "admin_id": row[0],
                    "franchisee_id": row[6],
                    "full_name": row[7] or row[1],
                    "email": row[1],
                    "mobile_no": row[2],
                    "username": row[1],
                    "password_hash": row[3],
                    "role": row[4],
                    "is_active": row[5],
                    "source": "vgf_platform_admins",
                }

    return None


def save_otp_code(mobile_number: str, otp_code: str, admin: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_phone_number(mobile_number)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            franchisee_id = admin.get("franchisee_id") or _fetch_default_franchisee_id(cur)
            cur.execute(
                """
                INSERT INTO vgf_adm_otp_sessions (
                    id, franchisee_id, mobile_number, otp_code, expires_at, verified,
                    created_at, added_by, added_date, added_time, added_ip,
                    last_updated_by, last_updated_date, last_updated_time, last_updated_ip,
                    is_active, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    franchisee_id,
                    normalized,
                    otp_code,
                    expires_at,
                    False,
                    now,
                    "system",
                    now.date(),
                    now.time().replace(microsecond=0),
                    "127.0.0.1",
                    "system",
                    now.date(),
                    now.time().replace(microsecond=0),
                    "127.0.0.1",
                    True,
                    False,
                ),
            )
            conn.commit()

    return {"mobile_number": normalized, "otp_code": otp_code, "expires_at": expires_at.isoformat()}


def send_otp_message(mobile_number: str, otp_code: str) -> str:
    if settings.app_env == "local":
        return f"Development OTP for {mobile_number}: {otp_code}"

    credentials = (
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_phone_number,
    )
    if not any(credentials):
        return "OTP service is not configured"
    if not all(credentials):
        raise RuntimeError(
            "Twilio credentials are incomplete. Configure all required settings."
        )

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    client.messages.create(
        body=f"Your Vigo Feast admin verification code is {otp_code}. It expires in 5 minutes.",
        from_=settings.twilio_phone_number,
        to=mobile_number,
    )
    return "OTP sent via Twilio"


def verify_otp_code(mobile_number: str, otp_code: str) -> dict[str, Any] | None:
    normalized = _normalize_phone_number(mobile_number)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, franchisee_id, mobile_number, otp_code, expires_at, verified, created_at
                FROM vgf_adm_otp_sessions
                WHERE mobile_number = %s AND is_active = TRUE AND is_deleted = FALSE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (normalized,),
            )
            row = cur.fetchone()
            if not row:
                return None

            expires_at = row[4]
            if expires_at < datetime.now(timezone.utc):
                return None

            if str(row[3]) != str(otp_code):
                return None

            cur.execute(
                "UPDATE vgf_adm_otp_sessions SET verified = TRUE, last_updated_by = %s, last_updated_date = %s, last_updated_time = %s, last_updated_ip = %s WHERE id = %s",
                (
                    "system",
                    datetime.now(timezone.utc).date(),
                    datetime.now(timezone.utc).time().replace(microsecond=0),
                    "127.0.0.1",
                    row[0],
                ),
            )
            conn.commit()
            admin = find_admin_by_mobile(normalized)
            if admin:
                return {"admin": admin, "otp_session_id": row[0], "verified": True}

    return None


def create_admin_session(admin: dict[str, Any], ip_address: str, user_agent: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    token = str(uuid.uuid4())
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM vgf_users WHERE mobile = %s OR email = %s LIMIT 1",
                (admin.get("mobile_no"), admin.get("email")),
            )
            user_row = cur.fetchone()
            user_id = user_row[0] if user_row else None
            franchisee_id = admin.get("franchisee_id")
            if isinstance(franchisee_id, str):
                try:
                    franchisee_id = uuid.UUID(franchisee_id)
                except ValueError:
                    franchisee_id = None
            if not isinstance(franchisee_id, uuid.UUID):
                franchisee_id = _fetch_default_franchisee_id(cur)
            session_actor = (
                admin.get("full_name")
                or admin.get("username")
                or admin.get("email")
                or "admin"
            )
            expires_at = now + timedelta(hours=12)
            session_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO vgf_adm_sessions (
                    id, franchisee_id, user_id, session_token, ip_address, user_agent, expires_at,
                    is_active, created_at, added_by, added_date, added_time, added_ip,
                    last_updated_by, last_updated_date, last_updated_time, last_updated_ip, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session_id,
                    franchisee_id,
                    user_id,
                    token,
                    ip_address,
                    user_agent,
                    expires_at,
                    True,
                    now,
                    session_actor,
                    now.date(),
                    now.time().replace(microsecond=0),
                    ip_address,
                    session_actor,
                    now.date(),
                    now.time().replace(microsecond=0),
                    ip_address,
                    False,
                ),
            )
            conn.commit()

    return {"session_id": session_id, "session_token": token, "expires_at": expires_at.isoformat()}
