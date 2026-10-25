from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from module44_backend.database import get_db
from module44_backend.services.dashboard import get_dashboard_summary


router = APIRouter(
    prefix="/api/admin/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
):
    return get_dashboard_summary(db)