import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


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


settings = Settings()
if not settings.jwt_secret.strip():
    raise RuntimeError(
        "JWT_SECRET is required and must not be empty. Set it in the environment or .env."
    )
