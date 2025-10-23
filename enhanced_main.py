import os
import smtplib
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
except ImportError:
    # Fallback for compatibility issues
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
import jwt
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Setup ---
app = FastAPI(title="Enhanced Electronics Store Inventory API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./enhanced_inventory.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Enhanced SQLAlchemy Models ---

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="cashier")  # admin, manager, cashier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

class Location(Base):
    __tablename__ = "locations"
    
    location_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(Text)
    manager_id = Column(Integer, ForeignKey("users.user_id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Supplier(Base):
    __tablename__ = "suppliers"
    
    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    contact_person = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    is_active = Column(Boolean, default=True)

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)

class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    cost = Column(Float)
    sku = Column(String, unique=True, index=True)
    upc = Column(String, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    reorder_level = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    requires_serial = Column(Boolean, default=False)
    requires_batch = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ProductLocation(Base):
    __tablename__ = "product_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (UniqueConstraint('product_id', 'location_id', name='_product_location_uc'),)

class BatchSerial(Base):
    __tablename__ = "batch_serials"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    batch_number = Column(String, index=True)
    serial_number = Column(String, unique=True, index=True)
    expiry_date = Column(DateTime)
    status = Column(String, default="available")  # available, sold, damaged, returned
    created_at = Column(DateTime, server_default=func.now())

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class Sale(Base):
    __tablename__ = "sales"
    
    sale_id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime, server_default=func.now())
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    total_amount = Column(Float)
    payment_method = Column(String)
    status = Column(String, default="completed")

class SaleItem(Base):
    __tablename__ = "sale_items"
    
    sale_item_id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_serial_id = Column(Integer, ForeignKey("batch_serials.id"), nullable=True)
    quantity = Column(Integer)
    price = Column(Float)
    discount = Column(Float, default=0)

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    batch_serial_id = Column(Integer, ForeignKey("batch_serials.id"), nullable=True)
    transaction_type = Column(String)  # receipt, sale, adjustment, transfer, return
    quantity_change = Column(Integer)
    transaction_date = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.user_id"))
    reference_id = Column(String)  # PO number, Sale ID, etc.
    notes = Column(Text)

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    po_id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    order_date = Column(DateTime, server_default=func.now())
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    status = Column(String, default="pending")  # pending, ordered, received, cancelled
    total_amount = Column(Float)
    created_by = Column(Integer, ForeignKey("users.user_id"))

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    
    po_item_id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.po_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity_ordered = Column(Integer)
    quantity_received = Column(Integer, default=0)
    unit_cost = Column(Float)

class ReorderAlert(Base):
    __tablename__ = "reorder_alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    current_stock = Column(Integer)
    reorder_level = Column(Integer)
    suggested_quantity = Column(Integer)
    status = Column(String, default="pending")  # pending, acknowledged, ordered, dismissed
    created_at = Column(DateTime, server_default=func.now())
    acknowledged_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    action = Column(String)
    table_name = Column(String)
    record_id = Column(Integer)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    timestamp = Column(DateTime, server_default=func.now())
    ip_address = Column(String)

# Create all tables
Base.metadata.create_all(bind=engine)

# --- Pydantic Models ---

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str = "cashier"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    manager_id: Optional[int] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    location_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    sku: Optional[str] = None
    upc: Optional[str] = None
    supplier_id: Optional[int] = None
    category_id: Optional[int] = None
    reorder_level: int = 10
    reorder_quantity: int = 50
    requires_serial: bool = False
    requires_batch: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None

class Product(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductLocationBase(BaseModel):
    product_id: int
    location_id: int
    stock_quantity: int = 0

class ProductLocationCreate(ProductLocationBase):
    pass

class ProductLocation(ProductLocationBase):
    id: int
    reserved_quantity: int
    last_updated: datetime
    
    class Config:
        from_attributes = True

class BatchSerialBase(BaseModel):
    product_id: int
    location_id: int
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[datetime] = None

class BatchSerialCreate(BatchSerialBase):
    pass

class BatchSerial(BatchSerialBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReorderAlertBase(BaseModel):
    product_id: int
    location_id: int
    current_stock: int
    reorder_level: int
    suggested_quantity: int

class ReorderAlert(ReorderAlertBase):
    alert_id: int
    status: str
    created_at: datetime
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- Utility Functions ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("Email credentials not configured")
        return False
    
    try:
        msg = MimeMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def check_reorder_levels(db: Session, background_tasks: BackgroundTasks):
    """Check all products for reorder levels and create alerts"""
    try:
        # Get all product locations with stock below reorder level
        low_stock_items = db.query(ProductLocation, Product).join(Product).filter(
            ProductLocation.stock_quantity <= Product.reorder_level
        ).all()
        
        for product_location, product in low_stock_items:
            # Check if alert already exists
            existing_alert = db.query(ReorderAlert).filter(
                ReorderAlert.product_id == product.product_id,
                ReorderAlert.location_id == product_location.location_id,
                ReorderAlert.status == "pending"
            ).first()
            
            if not existing_alert:
                # Create new reorder alert
                alert = ReorderAlert(
                    product_id=product.product_id,
                    location_id=product_location.location_id,
                    current_stock=product_location.stock_quantity,
                    reorder_level=product.reorder_level,
                    suggested_quantity=product.reorder_quantity
                )
                db.add(alert)
                
                # Send email notification
                location = db.query(Location).filter(Location.location_id == product_location.location_id).first()
                if location and location.manager_id:
                    manager = db.query(User).filter(User.user_id == location.manager_id).first()
                    if manager and manager.email:
                        subject = f"Reorder Alert: {product.name}"
                        body = f"""
                        <h2>Low Stock Alert</h2>
                        <p><strong>Product:</strong> {product.name}</p>
                        <p><strong>Location:</strong> {location.name}</p>
                        <p><strong>Current Stock:</strong> {product_location.stock_quantity}</p>
                        <p><strong>Reorder Level:</strong> {product.reorder_level}</p>
                        <p><strong>Suggested Reorder Quantity:</strong> {product.reorder_quantity}</p>
                        <p>Please consider placing a purchase order for this item.</p>
                        """
                        background_tasks.add_task(send_email, manager.email, subject, body)
        
        db.commit()
        logger.info(f"Reorder level check completed. Found {len(low_stock_items)} items below reorder level.")
        
    except Exception as e:
        logger.error(f"Error checking reorder levels: {str(e)}")
        db.rollback()

# --- Authentication Dependencies ---

async def get_current_user(token: str = Depends(lambda: ""), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    # For now, return a mock user - implement proper JWT validation in production
    return db.query(User).first()

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Operation requires one of these roles: {required_roles}"
            )
        return current_user
    return role_checker

# Import AI Analytics and Cloud Integrations
from ai_analytics import create_ai_analytics, DemandForecaster, PriceOptimizer, AutoReorderSystem
from cloud_integrations import create_integrations
from ecommerce_integrations import create_ecommerce_integrations
from returns_exchanges import create_returns_manager, ReturnCreate, ReturnUpdate, ExchangeCreate, WarrantyClaimCreate
from financial_reporting import create_financial_reporting_manager
from payment_gateways import create_payment_gateway_manager, PaymentCreate, RefundCreate
from two_factor_auth import create_2fa_manager, TwoFactorEnable, TwoFactorVerify, TwoFactorBackupVerify
from gift_card_system import create_gift_card_manager, GiftCardCreate, GiftCardRedeem, GiftCardBalance
from multi_language import create_multi_language_manager, LanguageCreate, TranslationCreate, ProductTranslationCreate
from advanced_ai import create_advanced_ai_manager
from dari_integration import setup_dari_integration, create_dari_integrator
from shipping_logistics import create_shipping_manager, ShipmentCreate, ShippingRateRequest, AddressCreate
from manufacturing_production import create_manufacturing_manager, BOMCreate, WorkOrderCreate, ProductionRunCreate, QualityCheckCreate
from erp_integrations import create_erp_manager, ERPConnectionCreate, SyncRequest
from iot_blockchain import create_iot_blockchain_manager, IoTDeviceCreate, SensorDataCreate, SupplyChainEventCreate

# --- API Endpoints ---

# AI Analytics Endpoints
@app.get("/analytics/demand-forecast/{product_id}")
async def get_demand_forecast(
    product_id: int,
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get AI-powered demand forecast for a product"""
    try:
        ai_analytics = create_ai_analytics(db)
        forecaster = ai_analytics["demand_forecaster"]
        
        result = forecaster.predict_demand(product_id, days_ahead)
        return result
    except Exception as e:
        logger.error(f"Error in demand forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/train-demand-model/{product_id}")
async def train_demand_model(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Train demand forecasting model for a product"""
    def train_model():
        try:
            ai_analytics = create_ai_analytics(db)
            forecaster = ai_analytics["demand_forecaster"]
            result = forecaster.train_demand_model(product_id)
            logger.info(f"Model training completed for product {product_id}: {result}")
        except Exception as e:
            logger.error(f"Model training failed for product {product_id}: {str(e)}")
    
    background_tasks.add_task(train_model)
    return {"message": "Model training started in background", "product_id": product_id}

@app.get("/analytics/price-optimization/{product_id}")
async def get_price_optimization(
    product_id: int,
    target_margin: float = 0.3,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get AI-powered price optimization suggestions"""
    try:
        # Get product cost
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        ai_analytics = create_ai_analytics(db)
        optimizer = ai_analytics["price_optimizer"]
        
        result = optimizer.optimize_price(product_id, product.cost or 0, target_margin)
        return result
    except Exception as e:
        logger.error(f"Error in price optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/price-elasticity/{product_id}")
async def get_price_elasticity(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get price elasticity analysis for a product"""
    try:
        ai_analytics = create_ai_analytics(db)
        optimizer = ai_analytics["price_optimizer"]
        
        result = optimizer.get_price_elasticity(product_id)
        return result
    except Exception as e:
        logger.error(f"Error calculating price elasticity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/reorder-suggestions")
async def get_reorder_suggestions(
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get AI-powered reorder suggestions"""
    try:
        ai_analytics = create_ai_analytics(db)
        auto_reorder = ai_analytics["auto_reorder"]
        
        suggestions = auto_reorder.generate_reorder_suggestions(location_id)
        return {"suggestions": suggestions, "count": len(suggestions)}
    except Exception as e:
        logger.error(f"Error generating reorder suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/reorder-calculation/{product_id}/{location_id}")
async def get_reorder_calculation(
    product_id: int,
    location_id: int,
    service_level: float = 0.95,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get detailed reorder point calculation for a product at a location"""
    try:
        ai_analytics = create_ai_analytics(db)
        auto_reorder = ai_analytics["auto_reorder"]
        
        result = auto_reorder.calculate_reorder_point(product_id, location_id, service_level)
        return result
    except Exception as e:
        logger.error(f"Error calculating reorder point: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/bulk-train-models")
async def bulk_train_models(
    background_tasks: BackgroundTasks,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Train demand forecasting models for all products (admin only)"""
    def train_all_models():
        try:
            # Get all products
            query = db.query(Product.product_id)
            if location_id:
                query = query.join(ProductLocation).filter(ProductLocation.location_id == location_id)
            
            product_ids = [p.product_id for p in query.all()]
            
            ai_analytics = create_ai_analytics(db)
            forecaster = ai_analytics["demand_forecaster"]
            
            results = []
            for product_id in product_ids:
                result = forecaster.train_demand_model(product_id)
                results.append({"product_id": product_id, "result": result})
                logger.info(f"Trained model for product {product_id}: {result}")
            
            logger.info(f"Bulk training completed for {len(product_ids)} products")
            
        except Exception as e:
            logger.error(f"Bulk model training failed: {str(e)}")
    
    background_tasks.add_task(train_all_models)
    return {"message": "Bulk model training started in background"}

# Cloud Integration Endpoints
@app.post("/cloud/backup/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create a database backup"""
    async def perform_backup():
        try:
            integrations = create_integrations(db)
            backup_manager = integrations["cloud_backup"]
            result = await backup_manager.create_database_backup()
            logger.info(f"Backup completed: {result}")
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
    
    background_tasks.add_task(perform_backup)
    return {"message": "Database backup started in background"}

@app.get("/cloud/backup/list")
async def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """List available backups"""
    try:
        integrations = create_integrations(db)
        backup_manager = integrations["cloud_backup"]
        backups = await backup_manager.list_backups()
        return {"backups": backups, "count": len(backups)}
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cloud/backup/restore")
async def restore_backup(
    backup_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Restore from backup"""
    async def perform_restore():
        try:
            integrations = create_integrations(db)
            backup_manager = integrations["cloud_backup"]
            result = await backup_manager.restore_from_backup(backup_path)
            logger.info(f"Restore completed: {result}")
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
    
    background_tasks.add_task(perform_restore)
    return {"message": "Database restore started in background", "backup_path": backup_path}

@app.get("/integrations/quickbooks/auth-url")
async def get_quickbooks_auth_url(
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get QuickBooks authorization URL"""
    try:
        integrations = create_integrations(None)
        quickbooks = integrations["quickbooks"]
        auth_url = quickbooks.get_authorization_url()
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"Error getting QB auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/integrations/quickbooks/sync-customers")
async def sync_customers_to_quickbooks(
    access_token: str,
    company_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Sync customers to QuickBooks"""
    async def perform_sync():
        try:
            integrations = create_integrations(db)
            quickbooks = integrations["quickbooks"]
            result = await quickbooks.sync_customers_to_quickbooks(access_token, company_id)
            logger.info(f"Customer sync completed: {result}")
        except Exception as e:
            logger.error(f"Customer sync failed: {str(e)}")
    
    background_tasks.add_task(perform_sync)
    return {"message": "Customer sync started in background"}

@app.post("/integrations/quickbooks/sync-sales")
async def sync_sales_to_quickbooks(
    access_token: str,
    company_id: str,
    start_date: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Sync sales to QuickBooks"""
    async def perform_sync():
        try:
            integrations = create_integrations(db)
            quickbooks = integrations["quickbooks"]
            
            start_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            
            result = await quickbooks.sync_sales_to_quickbooks(access_token, company_id, start_dt)
            logger.info(f"Sales sync completed: {result}")
        except Exception as e:
            logger.error(f"Sales sync failed: {str(e)}")
    
    background_tasks.add_task(perform_sync)
    return {"message": "Sales sync started in background"}

@app.post("/notifications/send-low-stock-alert")
async def send_low_stock_alert(
    manager_email: str,
    location_id: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Send low stock alert email"""
    async def send_alert():
        try:
            # Get low stock items
            ai_analytics = create_ai_analytics(db)
            auto_reorder = ai_analytics["auto_reorder"]
            suggestions = auto_reorder.generate_reorder_suggestions(location_id)
            
            if suggestions:
                integrations = create_integrations(db)
                email_system = integrations["email_notifications"]
                
                # Format for email
                low_stock_items = []
                for suggestion in suggestions:
                    low_stock_items.append({
                        'product_name': suggestion['product_name'],
                        'current_stock': suggestion['current_stock'],
                        'reorder_level': suggestion['reorder_level'],
                        'suggested_quantity': suggestion['suggested_order_quantity']
                    })
                
                result = await email_system.send_low_stock_alert(manager_email, low_stock_items)
                logger.info(f"Low stock alert sent: {result}")
            else:
                logger.info("No low stock items found")
                
        except Exception as e:
            logger.error(f"Failed to send low stock alert: {str(e)}")
    
    background_tasks.add_task(send_alert)
    return {"message": "Low stock alert email queued for sending"}

@app.post("/notifications/send-sales-report")
async def send_sales_report(
    recipient_email: str,
    report_period: str = "Last 30 Days",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Send sales report email"""
    async def send_report():
        try:
            # Generate report data
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Get sales summary
            sales_query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue
            FROM sales 
            WHERE sale_date >= :start_date
            """
            
            sales_result = db.execute(text(sales_query), {'start_date': thirty_days_ago}).fetchone()
            
            # Get top products
            top_products_query = """
            SELECT 
                p.name,
                SUM(si.quantity) as quantity_sold,
                SUM(si.quantity * si.price) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.sale_date >= :start_date
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT 5
            """
            
            top_products_result = db.execute(text(top_products_query), {'start_date': thirty_days_ago}).fetchall()
            
            report_data = {
                'total_sales': sales_result.total_sales or 0,
                'total_revenue': float(sales_result.total_revenue or 0),
                'top_products': [
                    {
                        'name': row.name,
                        'quantity_sold': row.quantity_sold,
                        'revenue': float(row.revenue)
                    }
                    for row in top_products_result
                ]
            }
            
            integrations = create_integrations(db)
            email_system = integrations["email_notifications"]
            
            result = await email_system.send_sales_report(recipient_email, report_data, report_period)
            logger.info(f"Sales report sent: {result}")
            
        except Exception as e:
            logger.error(f"Failed to send sales report: {str(e)}")
    
    background_tasks.add_task(send_report)
    return {"message": "Sales report email queued for sending"}

# E-commerce Integration Endpoints
@app.post("/ecommerce/shopify/sync-products")
async def sync_products_to_shopify(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Sync products to Shopify"""
    async def perform_sync():
        try:
            integrations = create_ecommerce_integrations(db)
            shopify = integrations["shopify"]
            result = await shopify.sync_products_to_shopify()
            logger.info(f"Shopify product sync completed: {result}")
        except Exception as e:
            logger.error(f"Shopify product sync failed: {str(e)}")
    
    background_tasks.add_task(perform_sync)
    return {"message": "Shopify product sync started in background"}

@app.post("/ecommerce/amazon/update-inventory")
async def update_amazon_inventory(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Update inventory on Amazon"""
    async def perform_update():
        try:
            integrations = create_ecommerce_integrations(db)
            amazon = integrations["amazon"]
            result = await amazon.update_amazon_inventory()
            logger.info(f"Amazon inventory update completed: {result}")
        except Exception as e:
            logger.error(f"Amazon inventory update failed: {str(e)}")
    
    background_tasks.add_task(perform_update)
    return {"message": "Amazon inventory update started in background"}

@app.get("/ecommerce/status")
async def get_ecommerce_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get e-commerce platform integration status"""
    try:
        integrations = create_ecommerce_integrations(db)
        manager = integrations["manager"]
        status = await manager.get_platform_status()
        return status
    except Exception as e:
        logger.error(f"Error getting e-commerce status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ecommerce/sync-all")
async def sync_all_platforms(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Sync inventory across all e-commerce platforms"""
    async def perform_sync():
        try:
            integrations = create_ecommerce_integrations(db)
            manager = integrations["manager"]
            result = await manager.sync_all_platforms()
            logger.info(f"Multi-platform sync completed: {result}")
        except Exception as e:
            logger.error(f"Multi-platform sync failed: {str(e)}")
    
    background_tasks.add_task(perform_sync)
    return {"message": "Multi-platform sync started in background"}

# Returns and Exchanges Endpoints
@app.post("/returns/")
async def create_return(
    return_data: ReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Create a new return request"""
    try:
        returns_manager = create_returns_manager(db)
        
        # Get customer ID from sale
        sale_query = "SELECT customer_id FROM sales WHERE sale_id = :sale_id"
        result = db.execute(text(sale_query), {'sale_id': return_data.sale_id})
        sale = result.fetchone()
        
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found")
        
        result = await returns_manager.create_return(return_data, sale.customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Return creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/returns/{return_id}")
async def process_return(
    return_id: int,
    update_data: ReturnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Process a return request"""
    try:
        returns_manager = create_returns_manager(db)
        result = await returns_manager.process_return(return_id, update_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Return processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/exchanges/")
async def create_exchange(
    exchange_data: ExchangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a product exchange"""
    try:
        returns_manager = create_returns_manager(db)
        result = await returns_manager.create_exchange(exchange_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Exchange creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/warranty-claims/")
async def create_warranty_claim(
    claim_data: WarrantyClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Create a warranty claim"""
    try:
        returns_manager = create_returns_manager(db)
        result = await returns_manager.create_warranty_claim(claim_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Warranty claim creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/returns/report")
async def get_returns_report(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get returns and exchanges report"""
    try:
        returns_manager = create_returns_manager(db)
        result = await returns_manager.get_returns_report(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Returns report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Financial Reporting Endpoints
@app.get("/reports/profit-loss")
async def get_profit_loss_report(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Generate profit and loss report"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        reporting_manager = create_financial_reporting_manager(db)
        result = await reporting_manager.generate_profit_loss_report(start_dt, end_dt)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"P&L report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/inventory-valuation")
async def get_inventory_valuation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Generate inventory valuation report"""
    try:
        reporting_manager = create_financial_reporting_manager(db)
        result = await reporting_manager.generate_inventory_valuation_report()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Inventory valuation report failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/customer-analysis")
async def get_customer_analysis_report(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Generate customer analysis report"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        reporting_manager = create_financial_reporting_manager(db)
        result = await reporting_manager.generate_customer_analysis_report(start_dt, end_dt)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Customer analysis report failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/sales-forecast")
async def get_sales_forecast(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Generate sales forecast"""
    try:
        reporting_manager = create_financial_reporting_manager(db)
        result = await reporting_manager.generate_sales_forecast(days_ahead)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Sales forecast generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/financial-metrics")
async def get_financial_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get financial dashboard data"""
    try:
        reporting_manager = create_financial_reporting_manager(db)
        result = await reporting_manager.generate_financial_dashboard_data()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Dashboard data generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Payment Gateway Endpoints
@app.post("/payments/create")
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Create a payment"""
    try:
        payment_manager = create_payment_gateway_manager(db)
        result = await payment_manager.create_payment(payment_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Payment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payments/{payment_id}/status")
async def get_payment_status(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Get payment status"""
    try:
        payment_manager = create_payment_gateway_manager(db)
        result = await payment_manager.get_payment_status(payment_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Payment status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payments/refund")
async def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a payment refund"""
    try:
        payment_manager = create_payment_gateway_manager(db)
        result = await payment_manager.create_refund(refund_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Refund creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Two-Factor Authentication Endpoints
@app.post("/auth/2fa/setup")
async def setup_2fa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Setup 2FA for current user"""
    try:
        tfa_manager = create_2fa_manager(db)
        result = await tfa_manager.setup_2fa(current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"2FA setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/2fa/enable")
async def enable_2fa(
    token_data: TwoFactorEnable,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enable 2FA after verification"""
    try:
        tfa_manager = create_2fa_manager(db)
        result = await tfa_manager.enable_2fa(current_user.user_id, token_data.token)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"2FA enable failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/2fa/verify")
async def verify_2fa(
    token_data: TwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verify 2FA token"""
    try:
        tfa_manager = create_2fa_manager(db)
        result = await tfa_manager.verify_2fa(current_user.user_id, token_data.token)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"2FA verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/2fa/status")
async def get_2fa_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get 2FA status for current user"""
    try:
        tfa_manager = create_2fa_manager(db)
        result = await tfa_manager.get_2fa_status(current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"2FA status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Gift Card Endpoints
@app.post("/gift-cards/")
async def create_gift_card(
    gift_card_data: GiftCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Create a new gift card"""
    try:
        gift_card_manager = create_gift_card_manager(db)
        result = await gift_card_manager.create_gift_card(gift_card_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Gift card creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gift-cards/balance")
async def check_gift_card_balance(
    balance_data: GiftCardBalance,
    db: Session = Depends(get_db)
):
    """Check gift card balance"""
    try:
        gift_card_manager = create_gift_card_manager(db)
        result = await gift_card_manager.check_balance(
            balance_data.card_number, 
            balance_data.pin_code
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Gift card balance check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gift-cards/redeem")
async def redeem_gift_card(
    redeem_data: GiftCardRedeem,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Redeem gift card"""
    try:
        gift_card_manager = create_gift_card_manager(db)
        result = await gift_card_manager.redeem_gift_card(
            redeem_data.card_number,
            redeem_data.amount,
            pin_code=redeem_data.pin_code,
            user_id=current_user.user_id
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Gift card redemption failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/gift-cards/analytics")
async def get_gift_card_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get gift card analytics"""
    try:
        gift_card_manager = create_gift_card_manager(db)
        result = await gift_card_manager.get_gift_card_analytics(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Gift card analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Multi-Language Endpoints
@app.get("/languages/")
async def get_languages(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get available languages"""
    try:
        ml_manager = create_multi_language_manager(db)
        result = await ml_manager.get_languages(active_only)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Language retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/languages/")
async def add_language(
    language_data: LanguageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Add a new language"""
    try:
        ml_manager = create_multi_language_manager(db)
        result = await ml_manager.add_language(language_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Language addition failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/translations/{language_code}")
async def get_translations(
    language_code: str,
    db: Session = Depends(get_db)
):
    """Get translations for a language"""
    try:
        ml_manager = create_multi_language_manager(db)
        result = await ml_manager.get_translations(language_code)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Translation retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translations/")
async def add_translation(
    translation_data: TranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Add or update a translation"""
    try:
        ml_manager = create_multi_language_manager(db)
        result = await ml_manager.add_translation(translation_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Translation addition failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/localized/{language_code}")
async def get_localized_products(
    language_code: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get products with translations"""
    try:
        ml_manager = create_multi_language_manager(db)
        result = await ml_manager.get_localized_products(language_code, limit, offset)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Localized products retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Dari Language Integration Endpoints
@app.post("/languages/dari/setup")
async def setup_dari_language_integration(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Setup complete Dari language integration"""
    try:
        result = await setup_dari_integration(db)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Dari integration setup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages/dari/formatting-rules")
async def get_dari_formatting_rules(
    db: Session = Depends(get_db)
):
    """Get Dari language formatting rules and guidelines"""
    try:
        dari_integrator = create_dari_integrator(db)
        rules = dari_integrator.get_dari_formatting_rules()
        
        return {
            "success": True,
            "formatting_rules": rules
        }
        
    except Exception as e:
        logger.error(f"Dari formatting rules retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/languages/dari/validate-text")
async def validate_dari_text(
    text: str,
    db: Session = Depends(get_db)
):
    """Validate Dari text for proper formatting"""
    try:
        dari_integrator = create_dari_integrator(db)
        result = await dari_integrator.validate_dari_text(text)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Dari text validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/languages/dari/add-categories")
async def add_dari_product_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Add Dari product categories"""
    try:
        dari_integrator = create_dari_integrator(db)
        result = await dari_integrator.add_dari_product_categories()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Dari categories addition failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced AI Endpoints
@app.post("/ai/analyze-product/{product_id}")
async def analyze_product_content(
    product_id: int,
    image_data: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Analyze product content with AI"""
    try:
        ai_manager = create_advanced_ai_manager(db)
        result = await ai_manager.analyze_product_content(product_id, image_data, description)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"AI product analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/insights")
async def get_ai_insights(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get AI-powered business insights"""
    try:
        ai_manager = create_advanced_ai_manager(db)
        result = await ai_manager.get_ai_insights(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"AI insights generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Shipping & Logistics Endpoints
@app.post("/shipping/rates")
async def get_shipping_rates(
    rate_request: ShippingRateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Get shipping rates from all carriers"""
    try:
        shipping_manager = create_shipping_manager(db)
        result = await shipping_manager.get_shipping_rates(rate_request)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Shipping rates request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shipping/shipments")
async def create_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "cashier"]))
):
    """Create a new shipment"""
    try:
        shipping_manager = create_shipping_manager(db)
        result = await shipping_manager.create_shipment(shipment_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Shipment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shipping/track/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Track shipment by tracking number"""
    try:
        shipping_manager = create_shipping_manager(db)
        result = await shipping_manager.track_shipment(tracking_number)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Shipment tracking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shipping/analytics")
async def get_shipping_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get shipping analytics"""
    try:
        shipping_manager = create_shipping_manager(db)
        result = await shipping_manager.get_shipping_analytics(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Shipping analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Manufacturing & Production Endpoints
@app.post("/manufacturing/bom")
async def create_bill_of_materials(
    bom_data: BOMCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create Bill of Materials"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.create_bom(bom_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"BOM creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manufacturing/work-orders")
async def create_work_order(
    work_order_data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create work order"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.create_work_order(work_order_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Work order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manufacturing/production-runs")
async def start_production_run(
    run_data: ProductionRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "operator"]))
):
    """Start production run"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.start_production_run(run_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Production run start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manufacturing/quality-checks")
async def create_quality_check(
    check_data: QualityCheckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "inspector"]))
):
    """Create quality check"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.create_quality_check(check_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Quality check creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manufacturing/schedule")
async def get_production_schedule(
    facility_id: Optional[int] = None,
    days_ahead: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get production schedule"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.get_production_schedule(facility_id, days_ahead)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Production schedule retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manufacturing/analytics")
async def get_manufacturing_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get manufacturing analytics"""
    try:
        manufacturing_manager = create_manufacturing_manager(db)
        result = await manufacturing_manager.get_manufacturing_analytics(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Manufacturing analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ERP Integration Endpoints
@app.post("/erp/connections")
async def create_erp_connection(
    connection_data: ERPConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Create ERP connection"""
    try:
        erp_manager = create_erp_manager(db)
        result = await erp_manager.create_erp_connection(connection_data, current_user.user_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"ERP connection creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/erp/test-connection/{connection_id}")
async def test_erp_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Test ERP connection"""
    try:
        erp_manager = create_erp_manager(db)
        result = await erp_manager.test_connection(connection_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"ERP connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/erp/sync")
async def sync_erp_data(
    sync_request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Sync data with ERP system"""
    try:
        erp_manager = create_erp_manager(db)
        result = await erp_manager.sync_data(sync_request)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"ERP data sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/erp/sync-history")
async def get_erp_sync_history(
    connection_id: Optional[int] = None,
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get ERP sync history"""
    try:
        erp_manager = create_erp_manager(db)
        result = await erp_manager.get_sync_history(connection_id, days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"ERP sync history retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/erp/analytics")
async def get_erp_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get ERP integration analytics"""
    try:
        erp_manager = create_erp_manager(db)
        result = await erp_manager.get_erp_analytics(days_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"ERP analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# IoT & Blockchain Endpoints
@app.post("/iot/devices")
async def register_iot_device(
    device_data: IoTDeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Register IoT device"""
    try:
        iot_manager = create_iot_blockchain_manager(db)
        result = await iot_manager.iot_manager.register_device(device_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"IoT device registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iot/sensor-data")
async def receive_sensor_data(
    sensor_data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """Receive sensor data from IoT devices"""
    try:
        iot_manager = create_iot_blockchain_manager(db)
        result = await iot_manager.iot_manager.receive_sensor_data(sensor_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Sensor data processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/iot/devices/{device_id}/analytics")
async def get_device_analytics(
    device_id: int,
    hours_back: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get IoT device analytics"""
    try:
        iot_manager = create_iot_blockchain_manager(db)
        result = await iot_manager.iot_manager.get_device_analytics(device_id, hours_back)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Device analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/blockchain/supply-chain-events")
async def create_supply_chain_event(
    event_data: SupplyChainEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create supply chain event on blockchain"""
    try:
        blockchain_manager = create_iot_blockchain_manager(db)
        result = await blockchain_manager.blockchain_manager.create_supply_chain_event(event_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Supply chain event creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blockchain/products/{product_id}/history")
async def get_product_blockchain_history(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get product supply chain history from blockchain"""
    try:
        blockchain_manager = create_iot_blockchain_manager(db)
        result = await blockchain_manager.blockchain_manager.get_product_history(product_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Product blockchain history failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blockchain/verify")
async def verify_blockchain_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Verify blockchain integrity"""
    try:
        blockchain_manager = create_iot_blockchain_manager(db)
        result = await blockchain_manager.blockchain_manager.verify_blockchain_integrity()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Blockchain verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/iot-blockchain-status")
async def get_iot_blockchain_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get IoT and blockchain system status"""
    try:
        system_manager = create_iot_blockchain_manager(db)
        result = await system_manager.get_system_status()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

# Location Endpoints
@app.post("/locations/", response_model=Location)
async def create_location(
    location: LocationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new location"""
    db_location = Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@app.get("/locations/", response_model=List[Location])
async def get_locations(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all locations"""
    locations = db.query(Location).filter(Location.is_active == True).offset(skip).limit(limit).all()
    return locations

# Enhanced Product Endpoints
@app.post("/products/", response_model=Product)
async def create_product(
    product: ProductCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new product"""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[Product])
async def get_products(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all products"""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}/locations", response_model=List[ProductLocation])
async def get_product_locations(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get stock levels for a product across all locations"""
    locations = db.query(ProductLocation).filter(ProductLocation.product_id == product_id).all()
    return locations

# Product Location Management
@app.post("/product-locations/", response_model=ProductLocation)
async def create_product_location(
    product_location: ProductLocationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Add a product to a location with initial stock"""
    # Check if product-location combination already exists
    existing = db.query(ProductLocation).filter(
        ProductLocation.product_id == product_location.product_id,
        ProductLocation.location_id == product_location.location_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists at this location")
    
    db_product_location = ProductLocation(**product_location.dict())
    db.add(db_product_location)
    db.commit()
    db.refresh(db_product_location)
    return db_product_location

@app.put("/product-locations/{product_id}/{location_id}/stock")
async def update_stock(
    product_id: int,
    location_id: int,
    quantity_change: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user)
):
    """Update stock quantity for a product at a specific location"""
    # Get product location
    product_location = db.query(ProductLocation).filter(
        ProductLocation.product_id == product_id,
        ProductLocation.location_id == location_id
    ).first()
    
    if not product_location:
        raise HTTPException(status_code=404, detail="Product not found at this location")
    
    # Calculate new stock
    new_stock = product_location.stock_quantity + quantity_change
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative")
    
    # Update stock
    product_location.stock_quantity = new_stock
    product_location.last_updated = datetime.utcnow()
    
    # Create inventory transaction
    transaction_type = "adjustment"
    if quantity_change > 0:
        transaction_type = "receipt"
    elif quantity_change < 0:
        transaction_type = "adjustment"
    
    db_transaction = InventoryTransaction(
        product_id=product_id,
        location_id=location_id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        user_id=current_user.user_id,
        notes=notes or f"Stock adjustment by {current_user.username}"
    )
    
    db.add(product_location)
    db.add(db_transaction)
    db.commit()
    
    # Check reorder levels in background
    background_tasks.add_task(check_reorder_levels, db, background_tasks)
    
    return {
        "product_id": product_id,
        "location_id": location_id,
        "new_stock_quantity": new_stock,
        "transaction_id": db_transaction.transaction_id
    }

# Batch/Serial Number Management
@app.post("/batch-serials/", response_model=BatchSerial)
async def create_batch_serial(
    batch_serial: BatchSerialCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Create a new batch or serial number entry"""
    db_batch_serial = BatchSerial(**batch_serial.dict())
    db.add(db_batch_serial)
    db.commit()
    db.refresh(db_batch_serial)
    return db_batch_serial

@app.get("/products/{product_id}/batch-serials", response_model=List[BatchSerial])
async def get_product_batch_serials(
    product_id: int,
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get batch/serial numbers for a product"""
    query = db.query(BatchSerial).filter(BatchSerial.product_id == product_id)
    
    if location_id:
        query = query.filter(BatchSerial.location_id == location_id)
    if status:
        query = query.filter(BatchSerial.status == status)
    
    return query.all()

# Reorder Alerts
@app.get("/reorder-alerts/", response_model=List[ReorderAlert])
async def get_reorder_alerts(
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Get reorder alerts"""
    query = db.query(ReorderAlert)
    
    if status:
        query = query.filter(ReorderAlert.status == status)
    if location_id:
        query = query.filter(ReorderAlert.location_id == location_id)
    
    return query.order_by(ReorderAlert.created_at.desc()).all()

@app.put("/reorder-alerts/{alert_id}/acknowledge")
async def acknowledge_reorder_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    """Acknowledge a reorder alert"""
    alert = db.query(ReorderAlert).filter(ReorderAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.user_id
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Alert acknowledged successfully"}

# Background task to check reorder levels periodically
@app.on_event("startup")
async def startup_event():
    """Run background tasks on startup"""
    logger.info("Enhanced Inventory API started successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
