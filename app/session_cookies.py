from fastapi import Response

from app.config import settings


def set_admin_auth_cookie(
    response: Response, token: str, remember_me: bool
) -> None:
    # Keep the signed credential out of JavaScript and persist it only when requested.
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.remember_me_ttl_seconds if remember_me else None,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain or None,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )


def clear_admin_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain or None,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
