import os
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from module45_backend import models
from module45_backend.database import get_db

app = FastAPI(title="NFDS Module 4 - Admin & Operations API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/")
async def root():
    return RedirectResponse(url="/module45/dashboard/4.5")


# ==========================================
# EXISTING API ENDPOINTS (Kept intact)
# ==========================================
@app.get("/api/module45/overview")
def get_ops_overview(db: Session = Depends(get_db)):
    in_progress = (
        db.query(models.VGFOrder)
        .filter(
            models.VGFOrder.status.in_(
                ["ORDERED", "PLACED", "CONFIRMED", "PREPARING", "READY_FOR_PICKUP", "OUT_FOR_DELIVERY"]
            )
        )
        .count()
    )
    cancelled = (
        db.query(models.VGFOrder)
        .filter(models.VGFOrder.status.in_(["CANCELLED", "REJECTED", "FAILED"]))
        .count()
    )
    return {
        "orders_in_progress": in_progress,
        "orders_delayed": 0,
        "avg_prep_time_mins": 0,
        "avg_delivery_time_mins": 0,
        "cancelled_today": cancelled,
        "sla_breaches": 0,
        "active_riders_online": 0,
    }


@app.get("/api/module45/live-orders")
def get_live_orders(db: Session = Depends(get_db)):
    return (
        db.query(models.VGFOrder)
        .filter(
            models.VGFOrder.status.in_(
                ["ORDERED", "PLACED", "CONFIRMED", "PREPARING", "READY_FOR_PICKUP", "OUT_FOR_DELIVERY"]
            )
        )
        .order_by(models.VGFOrder.created_at.desc())
        .all()
    )


# ==========================================
# 4.3 RESTAURANT MANAGEMENT & APPROVAL
# ==========================================
@app.get("/dashboard/4.3")
async def render_restaurant_dashboard(request: Request, db: Session = Depends(get_db)):
    restaurants = (
        db.query(models.VGFRestaurant)
        .filter(models.VGFRestaurant.is_deleted == False)  # noqa: E712
        .order_by(models.VGFRestaurant.created_at.desc())
        .all()
    )

    registrations = db.execute(
        text(
            """
            SELECT
                ra.id::text AS id,
                ra.restaurant_id::text AS restaurant_id,
                r.name AS restaurant_name,
                r.city,
                r.state,
                r.phone,
                r.email,
                r.address_line1,
                r.postal_code,
                ra.status,
                ra.submitted_at,
                ra.rejection_reason
            FROM vgf_restaurant_registration_applications ra
            LEFT JOIN vgf_restaurants r ON r.id = ra.restaurant_id
            WHERE COALESCE(ra.is_deleted, false) = false
            ORDER BY ra.submitted_at DESC NULLS LAST
            """
        )
    ).mappings().all()

    pending_apps = sum(
        1 for reg in registrations if (reg["status"] or "").upper() in {"SUBMITTED", "UNDER_REVIEW", "PENDING"}
    )

    documents = []
    try:
        documents = db.execute(
            text(
                """
                SELECT
                    d.id::text AS id,
                    d.restaurant_id::text AS restaurant_id,
                    d.document_type,
                    d.file_url,
                    d.file_name,
                    d.verification_status,
                    d.rejection_reason,
                    r.name AS restaurant_name
                FROM vgf_restaurant_documents d
                LEFT JOIN vgf_restaurants r ON r.id = d.restaurant_id
                WHERE COALESCE(d.is_deleted, false) = false
                ORDER BY r.name NULLS LAST, d.document_type
                LIMIT 100
                """
            )
        ).mappings().all()
    except Exception:
        db.rollback()

    menu_items = (
        db.query(models.VGFMenuItem)
        .filter(models.VGFMenuItem.is_deleted == False)  # noqa: E712
        .order_by(models.VGFMenuItem.created_at.desc())
        .limit(100)
        .all()
    )

    restaurant_map = {str(r.id): r.name for r in restaurants}

    return templates.TemplateResponse(
        "4.3_restaurants.html",
        {
            "request": request,
            "restaurants": restaurants,
            "registrations": registrations,
            "pending_apps": pending_apps,
            "documents": documents,
            "menu_items": menu_items,
            "restaurant_map": restaurant_map,
        },
    )


@app.post("/api/4.3/registrations/{app_id}/decision")
async def decide_restaurant_registration(
    app_id: str,
    decision: str = Form(...),
    rejection_reason: str = Form(""),
    db: Session = Depends(get_db),
):
    decision_upper = decision.strip().upper()
    if decision_upper not in {"APPROVED", "REJECTED", "UNDER_REVIEW"}:
        raise HTTPException(status_code=400, detail="Invalid decision")

    reg = db.execute(
        text(
            "SELECT restaurant_id::text AS restaurant_id FROM vgf_restaurant_registration_applications WHERE id::text = :id"
        ),
        {"id": app_id},
    ).mappings().first()

    if not reg:
        raise HTTPException(status_code=404, detail="Registration application not found")

    db.execute(
        text(
            """
            UPDATE vgf_restaurant_registration_applications
            SET status = :status,
                rejection_reason = :reason,
                reviewed_at = NOW(),
                last_updated_date = CURRENT_DATE,
                last_updated_time = CURRENT_TIME
            WHERE id::text = :id
            """
        ),
        {
            "id": app_id,
            "status": decision_upper,
            "reason": rejection_reason.strip() if decision_upper == "REJECTED" else None,
        },
    )

    new_rest_status = (
        "ACTIVE" if decision_upper == "APPROVED" else ("REJECTED" if decision_upper == "REJECTED" else "PENDING")
    )
    db.execute(
        text(
            """
            UPDATE vgf_restaurants
            SET status = :rest_status,
                is_active = :is_active,
                updated_at = NOW()
            WHERE id::text = :rid
            """
        ),
        {
            "rid": reg["restaurant_id"],
            "rest_status": new_rest_status,
            "is_active": decision_upper == "APPROVED",
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.3", status_code=303)


@app.post("/api/4.3/restaurants/{restaurant_id}/status")
async def update_restaurant_status(
    restaurant_id: str,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    clean_status = status.strip().upper()
    db.execute(
        text(
            """
            UPDATE vgf_restaurants
            SET status = :status,
                is_active = :is_active,
                updated_at = NOW()
            WHERE id::text = :id
            """
        ),
        {
            "id": restaurant_id,
            "status": clean_status,
            "is_active": clean_status in {"ACTIVE", "APPROVED"},
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.3", status_code=303)


@app.post("/api/4.3/documents/{doc_id}/verify")
async def verify_restaurant_document(
    doc_id: str,
    verification_status: str = Form(...),
    rejection_reason: str = Form(""),
    db: Session = Depends(get_db),
):
    clean_status = verification_status.strip().upper()
    db.execute(
        text(
            """
            UPDATE vgf_restaurant_documents
            SET verification_status = :st,
                rejection_reason = :reason,
                verified_at = CASE WHEN :st = 'VERIFIED' THEN NOW() ELSE verified_at END,
                last_updated_date = CURRENT_DATE,
                last_updated_time = CURRENT_TIME
            WHERE id::text = :id
            """
        ),
        {
            "st": clean_status,
            "reason": rejection_reason.strip() if clean_status == "REJECTED" else None,
            "id": doc_id,
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.3", status_code=303)


@app.post("/api/4.3/menu-items/{item_id}/availability")
async def update_menu_item_availability(
    item_id: str,
    availability_status: str = Form(...),
    db: Session = Depends(get_db),
):
    clean_avail = availability_status.strip().upper()
    db.execute(
        text(
            """
            UPDATE vgf_menu_items
            SET availability_status = :avail,
                is_active = :active,
                updated_at = NOW()
            WHERE id::text = :id
            """
        ),
        {
            "id": item_id,
            "avail": clean_avail,
            "active": clean_avail == "AVAILABLE",
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.3", status_code=303)


# ==========================================
# 4.5 ORDERS & OPERATIONS MONITORING
# ==========================================
@app.get("/dashboard/4.5")
async def render_orders_dashboard(request: Request, db: Session = Depends(get_db)):
    orders = db.execute(
        text(
            """
            SELECT
                o.id,
                o.order_number,
                o.status,
                o.order_status,
                o.total_amount,
                o.subtotal,
                o.delivery_fee,
                o.payment_method,
                o.rider_id,
                o.restaurant_id::text AS restaurant_id,
                o.customer_id,
                o.delivery_address,
                o.cancellation_status,
                o.cancellation_reason,
                o.created_at,
                r.name AS restaurant_name,
                c.name AS customer_name,
                COALESCE(p.payment_status, 'PENDING') AS payment_status
            FROM vgf_orders o
            LEFT JOIN vgf_restaurants r ON r.id = o.restaurant_id
            LEFT JOIN vgf_customers c ON c.customer_id = o.customer_id
            LEFT JOIN LATERAL (
                SELECT payment_status
                FROM vgf_payments
                WHERE order_id::text = o.id::text OR order_id::text = o.order_id::text
                ORDER BY created_at DESC
                LIMIT 1
            ) p ON true
            WHERE COALESCE(o.is_deleted, false) = false
            ORDER BY o.created_at DESC
            LIMIT 100
            """
        )
    ).mappings().all()

    riders = []
    try:
        riders = db.execute(
            text(
                """
                SELECT rider_id, full_name, status
                FROM vgf_delivery_partners
                WHERE rider_id IS NOT NULL
                ORDER BY full_name NULLS LAST
                """
            )
        ).mappings().all()
    except Exception:
        db.rollback()

    stage_counts = {
        "new_acceptance": sum(1 for o in orders if (o["status"] or "").upper() in {"NEW", "ORDERED", "PLACED"}),
        "preparing": sum(1 for o in orders if (o["status"] or "").upper() in {"CONFIRMED", "ACCEPTED", "PREPARING"}),
        "rider_pickup": sum(1 for o in orders if (o["status"] or "").upper() in {"READY_FOR_PICKUP", "ASSIGNED"}),
        "out_for_delivery": sum(1 for o in orders if (o["status"] or "").upper() in {"OUT_FOR_DELIVERY", "PICKED_UP"}),
        "delivered": sum(1 for o in orders if (o["status"] or "").upper() == "DELIVERED"),
        "cancelled_failed": sum(
            1 for o in orders if (o["status"] or "").upper() in {"CANCELLED", "REJECTED", "FAILED"}
        ),
    }
    active_count = (
        stage_counts["new_acceptance"]
        + stage_counts["preparing"]
        + stage_counts["rider_pickup"]
        + stage_counts["out_for_delivery"]
    )

    return templates.TemplateResponse(
        "4.5_orders.html",
        {
            "request": request,
            "orders": orders,
            "riders": riders,
            "active_count": active_count,
            "stage_counts": stage_counts,
        },
    )


@app.post("/api/4.5/orders/{order_id}/update")
async def update_order_operations(
    order_id: str,
    status: str = Form(...),
    rider_id: str = Form(""),
    cancellation_reason: str = Form(""),
    db: Session = Depends(get_db),
):
    clean_status = status.strip().upper()
    rider_val: Optional[int] = int(rider_id) if rider_id.strip().isdigit() else None
    is_cancelled = clean_status in {"CANCELLED", "REJECTED", "FAILED"}

    db.execute(
        text(
            """
            UPDATE vgf_orders
            SET status = :status,
                order_status = :status,
                rider_id = COALESCE(:rider_id, rider_id),
                cancellation_status = CASE WHEN :is_cancelled THEN :status ELSE cancellation_status END,
                cancellation_reason = CASE WHEN :is_cancelled AND :reason <> '' THEN :reason ELSE cancellation_reason END,
                cancelled_by = CASE WHEN :is_cancelled THEN 'ADMIN' ELSE cancelled_by END,
                updated_at = NOW()
            WHERE id = :id
            """
        ),
        {
            "id": order_id,
            "status": clean_status,
            "rider_id": rider_val,
            "is_cancelled": is_cancelled,
            "reason": cancellation_reason.strip(),
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.5", status_code=303)


# ==========================================
# 4.6 REPORTS, ANALYTICS & CONFIGURATION
# ==========================================
@app.get("/dashboard/4.6")
async def render_reports_dashboard(request: Request, db: Session = Depends(get_db)):
    sales_summary = db.execute(
        text(
            """
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COALESCE(SUM(commission_amount), 0) AS total_commission,
                COALESCE(SUM(CASE WHEN created_at >= CURRENT_DATE THEN total_amount ELSE 0 END), 0) AS daily_sales,
                COALESCE(SUM(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN total_amount ELSE 0 END), 0) AS weekly_sales,
                COALESCE(SUM(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN total_amount ELSE 0 END), 0) AS monthly_sales,
                COUNT(*) AS total_orders
            FROM vgf_orders
            WHERE COALESCE(is_deleted, false) = false
              AND UPPER(COALESCE(status, '')) NOT IN ('CANCELLED', 'REJECTED')
            """
        )
    ).mappings().first()

    restaurant_revenue = db.execute(
        text(
            """
            SELECT
                r.name AS restaurant_name,
                r.city,
                COUNT(o.id) AS order_count,
                COALESCE(SUM(o.total_amount), 0) AS gross_revenue,
                COALESCE(SUM(o.commission_amount), 0) AS commission_earned
            FROM vgf_restaurants r
            LEFT JOIN vgf_orders o
                ON o.restaurant_id = r.id
               AND COALESCE(o.is_deleted, false) = false
            WHERE COALESCE(r.is_deleted, false) = false
            GROUP BY r.id, r.name, r.city
            ORDER BY gross_revenue DESC
            LIMIT 25
            """
        )
    ).mappings().all()

    customer_reports = db.execute(
        text(
            """
            SELECT
                c.customer_id,
                c.name AS customer_name,
                c.mobile,
                COUNT(o.id) AS total_orders,
                COALESCE(SUM(o.total_amount), 0) AS total_spent
            FROM vgf_customers c
            LEFT JOIN vgf_orders o
                ON o.customer_id = c.customer_id
               AND COALESCE(o.is_deleted, false) = false
            GROUP BY c.customer_id, c.name, c.mobile
            ORDER BY total_spent DESC
            LIMIT 25
            """
        )
    ).mappings().all()

    rider_performance = []
    try:
        rider_performance = db.execute(
            text(
                """
                SELECT
                    dp.rider_id,
                    dp.full_name AS rider_name,
                    dp.status,
                    COUNT(o.id) AS assigned_orders,
                    SUM(CASE WHEN UPPER(COALESCE(o.status, '')) = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered_orders
                FROM vgf_delivery_partners dp
                LEFT JOIN vgf_orders o ON o.rider_id = dp.rider_id
                WHERE dp.rider_id IS NOT NULL
                GROUP BY dp.rider_id, dp.full_name, dp.status
                ORDER BY delivered_orders DESC
                LIMIT 25
                """
            )
        ).mappings().all()
    except Exception:
        db.rollback()

    payment_reports = []
    try:
        payment_reports = db.execute(
            text(
                """
                SELECT
                    COALESCE(method, 'UNKNOWN') AS method,
                    COALESCE(payment_status, 'UNKNOWN') AS status,
                    COUNT(*) AS tx_count,
                    COALESCE(SUM(amount), 0) AS total_amount
                FROM vgf_payments
                WHERE COALESCE(is_deleted, false) = false
                GROUP BY method, payment_status
                ORDER BY total_amount DESC
                """
            )
        ).mappings().all()
    except Exception:
        db.rollback()

    commissions = (
        db.query(models.VGFCommissionRule)
        .filter(models.VGFCommissionRule.is_deleted == False)  # noqa: E712
        .order_by(models.VGFCommissionRule.rule_id.desc())
        .all()
    )

    ops_settings = None
    try:
        ops_settings = db.execute(
            text("SELECT * FROM vgf_delivery_operations_settings WHERE setting_id = 1")
        ).mappings().first()
    except Exception:
        db.rollback()

    return templates.TemplateResponse(
        "4.6_reports.html",
        {
            "request": request,
            "total_revenue": sales_summary["total_revenue"] if sales_summary else 0,
            "sales_summary": sales_summary,
            "restaurant_revenue": restaurant_revenue,
            "customer_reports": customer_reports,
            "rider_performance": rider_performance,
            "payment_reports": payment_reports,
            "commissions": commissions,
            "ops_settings": ops_settings,
        },
    )


@app.post("/api/4.6/commissions")
async def create_or_update_commission_rule(
    party_type: str = Form(...),
    commission_type: str = Form(...),
    commission_rate: float = Form(...),
    effective_from: str = Form(...),
    status: str = Form("ACTIVE"),
    db: Session = Depends(get_db),
):
    db.execute(
        text(
            """
            INSERT INTO vgf_commission_rules (
                party_type, commission_type, commission_rate, effective_from, status, is_active, is_deleted
            )
            VALUES (:party_type, :commission_type, :commission_rate, :effective_from, :status, :is_active, false)
            """
        ),
        {
            "party_type": party_type.strip().upper(),
            "commission_type": commission_type.strip().upper(),
            "commission_rate": commission_rate,
            "effective_from": effective_from,
            "status": status.strip().upper(),
            "is_active": status.strip().upper() == "ACTIVE",
        },
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.6", status_code=303)


@app.post("/api/4.6/operations-settings")
async def update_operational_settings(
    dispatch_mode: str = Form("RIDER_POOL"),
    max_active_orders: int = Form(3),
    db: Session = Depends(get_db),
):
    db.execute(
        text(
            """
            UPDATE vgf_delivery_operations_settings
            SET dispatch_mode = :mode,
                max_active_orders = :max_orders,
                updated_at = NOW()
            WHERE setting_id = 1
            """
        ),
        {"mode": dispatch_mode.strip().upper(), "max_orders": max_active_orders},
    )
    db.commit()
    return RedirectResponse(url="/module45/dashboard/4.6", status_code=303)