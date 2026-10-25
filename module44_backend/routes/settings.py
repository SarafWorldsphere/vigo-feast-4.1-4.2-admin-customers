from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from module44_backend.database import get_db
from module44_backend.services.settings import get_settings_summary


router = APIRouter(
    prefix="/api/admin/settings",
    tags=["Settings"],
)


@router.get("/summary")
def settings_summary(
    db: Session = Depends(get_db),
):
    return get_settings_summary(db)