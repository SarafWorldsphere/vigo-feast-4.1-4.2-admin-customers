
"""Configuration for the integrated Module 4.4 API."""

from app.config import settings as app_settings
from sqlalchemy.engine import URL


class Settings:
    app_name = "VIGO FEAST Admin Console"
    app_env = app_settings.app_env
    app_version = "1.0.0"
    db_schema = "public"
    db_table_prefix = "vgf_"
    default_page_size = 20
    max_page_size = 100

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=app_settings.db_user,
            password=app_settings.db_password,
            host=app_settings.db_host,
            port=app_settings.db_port,
            database=app_settings.db_name,
        )


settings = Settings()
