import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from app.config import settings


def password_reset_email_is_configured() -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_sender
        and settings.public_base_url
        and bool(settings.smtp_username) == bool(settings.smtp_password)
    )


def send_password_reset_email(recipient: str, token: str) -> None:
    if not password_reset_email_is_configured():
        raise RuntimeError("Password reset email delivery is not configured.")

    reset_url = (
        f"{settings.public_base_url}{settings.password_reset_path}"
        f"?{urlencode({'reset_token': token})}"
    )
    message = EmailMessage()
    message["Subject"] = settings.password_reset_email_subject
    message["From"] = settings.smtp_sender
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your Vigo Feast admin account. "
        "Use the link below to choose a new password. "
        f"The link expires in {settings.password_reset_ttl_seconds} seconds.\n\n"
        f"{reset_url}\n\n"
        "If you did not request this change, you can ignore this email."
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
            context=ssl.create_default_context(),
        ) as server:
            _send_message(server, message)
    else:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        ) as server:
            if settings.smtp_starttls:
                server.starttls(context=ssl.create_default_context())
            _send_message(server, message)


def _send_message(server: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
    server.send_message(message)
