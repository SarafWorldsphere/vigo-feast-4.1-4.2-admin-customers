
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import require_admin_auth
from module44_backend.database import get_db
from module44_backend.services.payment import get_payments


router = APIRouter(
    prefix="/api/admin/payments",
    tags=["Payment Management"],
    dependencies=[Depends(require_admin_auth)],
)


@router.get("/")
def list_payments(
    search: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=30),
    method: str | None = Query(default=None, max_length=30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_payments(
        db=db,
        search=search,
        status=status,
        method=method,
        page=page,
        page_size=page_size,
    )
