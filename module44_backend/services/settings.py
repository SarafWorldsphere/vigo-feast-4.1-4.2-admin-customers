from sqlalchemy import func
from sqlalchemy.orm import Session

from module44_backend.models.franchisee import Franchisee
from module44_backend.models.commission_rule import CommissionRule
from module44_backend.models.role import Role
from module44_backend.models.ref_status import RefStatus


def get_settings_summary(db: Session):
    franchisees = (
        db.query(Franchisee)
        .filter(
            Franchisee.is_deleted.is_(False),
        )
        .order_by(Franchisee.franchisee_name.asc())
        .all()
    )

    commission_rules = (
        db.query(CommissionRule)
        .filter(
            CommissionRule.is_deleted.is_(False),
        )
        .order_by(CommissionRule.rule_id.desc())
        .all()
    )

    roles = (
        db.query(Role)
        .filter(
            Role.is_deleted.is_(False),
        )
        .order_by(Role.role_name.asc())
        .all()
    )

    reference_statuses = (
        db.query(RefStatus)
        .filter(
            RefStatus.is_deleted.is_(False),
        )
        .order_by(RefStatus.status_name.asc())
        .all()
    )

    return {
        "franchisees": [
            {
                "id": str(item.id),
                "franchisee_name": item.franchisee_name,
                "is_active": item.is_active,
                "created_at": (
                    item.created_at.isoformat()
                    if item.created_at
                    else None
                ),
                "updated_at": (
                    item.updated_at.isoformat()
                    if item.updated_at
                    else None
                ),
            }
            for item in franchisees
        ],
        "commission_rules": [
            {
                "rule_id": item.rule_id,
                "party_type": item.party_type,
                "commission_type": item.commission_type,
                "commission_rate": (
                    float(item.commission_rate)
                    if item.commission_rate is not None
                    else None
                ),
                "effective_from": (
                    item.effective_from.isoformat()
                    if item.effective_from
                    else None
                ),
                "effective_to": (
                    item.effective_to.isoformat()
                    if item.effective_to
                    else None
                ),
                "status": item.status,
                "franchisee_id": (
                    str(item.franchisee_id)
                    if item.franchisee_id
                    else None
                ),
                "is_active": item.is_active,
            }
            for item in commission_rules
        ],
        "roles": [
            {
                "role_id": item.role_id,
                "role_name": item.role_name,
                "franchisee_id": (
                    str(item.franchisee_id)
                    if item.franchisee_id
                    else None
                ),
                "is_active": item.is_active,
            }
            for item in roles
        ],
        "reference_statuses": [
            {
                "id": str(item.id),
                "status_code": item.status_code,
                "status_name": item.status_name,
                "description": item.description,
                "is_active": item.is_active,
            }
            for item in reference_statuses
        ],
    }