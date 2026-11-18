from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from module45_backend.database import Base


# 1. CANONICAL ORDERS MODEL
class VGFOrder(Base):
    __tablename__ = "vgf_orders"

    id = Column(String(36), primary_key=True, index=True)
    order_number = Column(String(50), nullable=False, unique=True)
    customer_id = Column(Integer, nullable=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=True)
    rider_id = Column(Integer, nullable=True)
    delivery_address = Column(Text)
    delivery_fee = Column(Float, default=0.0)
    status = Column(String(50), index=True)
    order_status = Column(String(50))
    subtotal = Column(Numeric(10, 2), default=0)
    gst_amount = Column(Numeric(10, 2), default=0)
    delivery_charge = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), default=0)
    commission_rate = Column(Numeric(5, 4))
    commission_amount = Column(Numeric(10, 2))
    payment_method = Column(String(50))
    cancellation_status = Column(String(50))
    cancellation_reason = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# 2. MODELS FOR DASHBOARDS 4.3, 4.5, AND 4.6
class VGFRestaurant(Base):
    __tablename__ = "vgf_restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    phone = Column(String(30))
    email = Column(String(255))
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default="ACTIVE")
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))


class VGFRestaurantRegistration(Base):
    __tablename__ = "vgf_restaurant_registration_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)


class VGFMenuItem(Base):
    __tablename__ = "vgf_menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    restaurant_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    base_price = Column(Numeric(10, 2), nullable=False)
    food_type = Column(String(20), nullable=False)
    preparation_time_minutes = Column(Integer)
    availability_status = Column(String(20), nullable=False, default="AVAILABLE")
    is_active = Column(Boolean, nullable=False, default=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True))


class VGFCommissionRule(Base):
    __tablename__ = "vgf_commission_rules"

    rule_id = Column(Integer, primary_key=True, index=True)
    party_type = Column(String(30), nullable=False)
    commission_type = Column(String(30), nullable=False)
    commission_rate = Column(Numeric(7, 4))
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date)
    status = Column(String(20), nullable=False, default="ACTIVE")
    franchisee_id = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)


# 3. MONITORING TABLES (Kept intact)
class VGFSlaBreach(Base):
    __tablename__ = "VGF_sla_breaches"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String)
    breach_type = Column(String)
    excess_time_mins = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class VGFDelayAlert(Base):
    __tablename__ = "VGF_delay_alerts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String)
    alert_level = Column(String)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class VGFRiderLiveLocation(Base):
    __tablename__ = "VGF_rider_live_locations"

    id = Column(Integer, primary_key=True, index=True)
    rider_name = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    status = Column(String)