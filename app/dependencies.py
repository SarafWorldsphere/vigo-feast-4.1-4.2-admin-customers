from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request

from app.auth import decode_token
from app.config import settings
from app.db import get_db_connection

def require_admin_auth(
    request: Request,
) -> dict[str, Any]:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Authentication required") from exc

    session_id = payload.get("session_id")
    try:
        session_id = UUID(str(session_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Authentication required") from exc
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM vgf_adm_sessions
                WHERE id = %s
                  AND is_active IS TRUE
                  AND is_deleted IS FALSE
                  AND expires_at > NOW()
                """,
                (session_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=401, detail="Authentication required")

    role = payload.get("role")
    if not role:
        raise HTTPException(status_code=401, detail="Token missing role")

    action_column = {
        "GET": "can_view",
        "HEAD": "can_view",
        "POST": "can_create",
        "PUT": "can_update",
        "PATCH": "can_update",
        "DELETE": "can_delete",
    }.get(request.method)
    if action_column is None:
        raise HTTPException(status_code=403, detail="This action is not permitted")
    permission_found = False
    permission_granted = False
    franchisee_id = payload.get("franchisee_id")
    if isinstance(franchisee_id, str):
        try:
            franchisee_id = UUID(franchisee_id)
        except ValueError:
            pass
    franchisee_filter = "" if isinstance(franchisee_id, UUID) else " AND franchisee_id = %s"
    permission_parameters = (
        (role,) if isinstance(franchisee_id, UUID) else (role, franchisee_id)
    )
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT can_view, can_create, can_update, can_delete
                FROM vgf_adm_role_permission
                WHERE role_name = %s
                  AND permission_name = 'admin_console'
                  {franchisee_filter}
                  AND is_active IS TRUE
                """,
                permission_parameters,
            )
            permission = cur.fetchone()
            if permission:
                permission_found = True
                permission_index = {
                    "can_view": 0,
                    "can_create": 1,
                    "can_update": 2,
                    "can_delete": 3,
                }[action_column]
                permission_granted = bool(permission[permission_index])
    if permission_found and not permission_granted:
        raise HTTPException(status_code=403, detail="This action is not permitted")
    if not permission_found and str(role).lower() != "admin":
        raise HTTPException(status_code=403, detail="This role has no admin permissions")

    return payload

