import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.config import settings
from app.db import get_db_connection


OTP_SMS_TEXTS = {
    "english": (
        "Your mobile verification OTP is {otp_code} for VIGOFEAST. "
        "It is valid for 10 minutes. Do not share this OTP with anyone.\n"
        "- SARAF WORLDSPHERE AI SERVICES"
    ),
    "hindi": (
        "आपका मोबाइल सत्यापन OTP {otp_code} VIGOFEAST के लिए है। यह 10 मिनट तक मान्य है। इस OTP को किसी के साथ साझा न करें।\n"
        "- SARAF WORLDSPHERE AI SERVICES"
    ),
    "telugu": (
        "మీ మొబైల్ ధృవీకరణ OTP {otp_code} VIGOFEAST కోసం. "
        "ఇది 10 నిమిషాల వరకు చెల్లుబాటు అవుతుంది. "
        "ఈ OTP ని ఎవరితోనూ పంచుకోవద్దు.\n"
        "- SARAF WORLDSPHERE AI SERVICES"
    ),
}


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
    expires_at = now + timedelta(minutes=10)

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


def send_otp_message(
    mobile_number: str, otp_code: str, language: str = "english"
) -> str:
    if settings.app_env == "local":
        return f"Development OTP for {mobile_number}: {otp_code}"

    language_settings = {
        "english": (
            settings.nimbus_user_id,
            settings.nimbus_password,
            settings.nimbus_sender_id,
            settings.nimbus_entity_id,
            settings.nimbus_template_id,
        ),
        "hindi": (
            settings.nimbus_user_id_hindi,
            settings.nimbus_password_hindi,
            settings.nimbus_sender_id_hindi,
            settings.nimbus_entity_id_hindi,
            settings.nimbus_template_id_hindi,
        ),
        "telugu": (
            settings.nimbus_user_id_telugu,
            settings.nimbus_password_telugu,
            settings.nimbus_sender_id_telugu,
            settings.nimbus_entity_id_telugu,
            settings.nimbus_template_id_telugu,
        ),
    }
    credentials = language_settings.get(language, language_settings["english"])
    if not all(value.strip() for value in credentials):
        credentials = language_settings["english"]
    if not all(value.strip() for value in credentials):
        raise RuntimeError(
            "Nimbus SMS credentials are incomplete. Configure all required settings."
        )

    user_id, password, sender_id, entity_id, template_id = credentials
    message_template = OTP_SMS_TEXTS.get(language) or OTP_SMS_TEXTS["english"]
    message = message_template.format(otp_code=otp_code)

    phone_number = "".join(
        character for character in mobile_number if character in "0123456789"
    )
    if len(phone_number) == 12 and phone_number.startswith("91"):
        phone_number = phone_number[2:]
    if len(phone_number) != 10:
        raise ValueError("Mobile number must contain a 10-digit Indian phone number.")

    query = urllib.parse.urlencode(
        {
            "UserID": user_id,
            "Password": password,
            "SenderID": sender_id,
            "Phno": phone_number,
            "Msg": message,
            "EntityID": entity_id,
            "TemplateID": template_id,
        }
    )
    api_name = "SendSingleApi" if message.isascii() else "SendSingleUnicodeApi"
    request_url = f"http://nimbusit.biz/api/SmsApi/{api_name}?" + query

    try:
        with urllib.request.urlopen(request_url, timeout=15) as response:
            response_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Nimbus SMS request failed with HTTP status {exc.code}."
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Nimbus SMS request failed.") from None

    response_text = response_body.strip()
    response_lower = response_text.lower()
    response_has_error = any(
        marker in response_lower
        for marker in ("error", "failed", "failure", "invalid", "rejected")
    )
    try:
        response_data = json.loads(response_text)
    except json.JSONDecodeError:
        response_data = None

    if isinstance(response_data, dict):
        response_has_error = response_has_error or bool(response_data.get("error"))
        response_has_error = response_has_error or response_data.get("success") is False
        status = response_data.get("status")
        if isinstance(status, str):
            response_has_error = response_has_error or any(
                marker in status.lower()
                for marker in ("error", "fail", "invalid", "reject")
            )

    if response_has_error:
        raise RuntimeError("Nimbus SMS provider returned an error response.")

    return "OTP sent via Nimbus"


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
