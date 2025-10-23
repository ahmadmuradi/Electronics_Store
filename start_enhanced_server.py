#!/usr/bin/env python3
"""
Enhanced Electronics Store Inventory System - Server Startup Script
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        sys.exit(1)
    logger.info(f"Python version: {sys.version}")

def install_requirements():
    """Install required packages"""
    requirements_file = Path(__file__).parent / "requirements_minimal.txt"
    
    if not requirements_file.exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    logger.info("Installing required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        logger.info("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        sys.exit(1)

def setup_environment():
    """Setup environment variables with defaults"""
    env_vars = {
        'DATABASE_URL': 'sqlite:///./enhanced_inventory.db',
        'SECRET_KEY': 'your-secret-key-change-in-production',
        'SMTP_SERVER': 'smtp.gmail.com',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': '',
        'SMTP_PASSWORD': '',
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',
        'AWS_REGION': 'us-east-1',
        'BACKUP_BUCKET_NAME': 'electronics-store-backups',
        'QUICKBOOKS_CLIENT_ID': '',
        'QUICKBOOKS_CLIENT_SECRET': '',
        'COMPANY_NAME': 'Electronics Store'
    }
    
    logger.info("Setting up environment variables...")
    for key, default_value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = default_value
            if key in ['SMTP_USERNAME', 'SMTP_PASSWORD', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
                logger.warning(f"{key} not set - related features will be disabled")
            else:
                logger.info(f"Set {key} to default value")

def create_directories():
    """Create necessary directories"""
    directories = ['models', 'backups', 'logs']
    
    for directory in directories:
        dir_path = Path(__file__).parent / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def initialize_database():
    """Initialize database with sample data"""
    logger.info("Initializing database...")
    
    try:
        # Import here to avoid circular imports
        from enhanced_main import Base, engine, SessionLocal
        from enhanced_main import User, Location, Category, Supplier, Product, ProductLocation
        from passlib.context import CryptContext
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Create sample data
        db = SessionLocal()
        try:
            # Check if admin user exists
            admin_user = db.query(User).filter(User.username == 'admin').first()
            if not admin_user:
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                # Create admin user
                admin_user = User(
                    username='admin',
                    email='admin@electronicsstore.com',
                    full_name='System Administrator',
                    role='admin',
                    hashed_password=pwd_context.hash('admin123'),
                    is_active=True
                )
                db.add(admin_user)
                
                # Create manager user
                manager_user = User(
                    username='manager',
                    email='manager@electronicsstore.com',
                    full_name='Store Manager',
                    role='manager',
                    hashed_password=pwd_context.hash('manager123'),
                    is_active=True
                )
                db.add(manager_user)
                
                # Create cashier user
                cashier_user = User(
                    username='cashier',
                    email='cashier@electronicsstore.com',
                    full_name='Store Cashier',
                    role='cashier',
                    hashed_password=pwd_context.hash('cashier123'),
                    is_active=True
                )
                db.add(cashier_user)
                
                db.commit()
                logger.info("Sample users created")
            
            # Check if locations exist
            main_location = db.query(Location).filter(Location.name == 'Main Store').first()
            if not main_location:
                main_location = Location(
                    name='Main Store',
                    address='123 Main Street, City, State 12345',
                    manager_id=2,  # Manager user
                    is_active=True
                )
                db.add(main_location)
                
                warehouse_location = Location(
                    name='Warehouse',
                    address='456 Industrial Blvd, City, State 12345',
                    manager_id=2,
                    is_active=True
                )
                db.add(warehouse_location)
                
                db.commit()
                logger.info("Sample locations created")
            
            # Check if categories exist
            electronics_category = db.query(Category).filter(Category.name == 'Electronics').first()
            if not electronics_category:
                categories = [
                    Category(name='Electronics', description='Electronic devices and components'),
                    Category(name='Computers', description='Computers and accessories'),
                    Category(name='Mobile Devices', description='Smartphones and tablets'),
                    Category(name='Audio/Video', description='Audio and video equipment')
                ]
                
                for category in categories:
                    db.add(category)
                
                db.commit()
                logger.info("Sample categories created")
            
            # Check if suppliers exist
            tech_supplier = db.query(Supplier).filter(Supplier.name == 'Tech Distributors Inc').first()
            if not tech_supplier:
                suppliers = [
                    Supplier(
                        name='Tech Distributors Inc',
                        contact_person='John Smith',
                        phone='555-0123',
                        email='orders@techdist.com',
                        address='789 Tech Park, Silicon Valley, CA 94000',
                        is_active=True
                    ),
                    Supplier(
                        name='Electronics Wholesale Co',
                        contact_person='Jane Doe',
                        phone='555-0456',
                        email='sales@elecwholesale.com',
                        address='321 Commerce St, Business City, TX 75000',
                        is_active=True
                    )
                ]
                
                for supplier in suppliers:
                    db.add(supplier)
                
                db.commit()
                logger.info("Sample suppliers created")
            
            logger.info("Database initialization completed")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

def start_server():
    """Start the FastAPI server"""
    logger.info("Starting Enhanced Electronics Store Inventory Server...")
    
    try:
        import uvicorn
        uvicorn.run(
            "enhanced_main:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("=" * 60)
    print("Enhanced Electronics Store Inventory System")
    print("=" * 60)
    
    try:
        check_python_version()
        install_requirements()
        setup_environment()
        create_directories()
        initialize_database()
        
        print("\n" + "=" * 60)
        print("🚀 Server starting...")
        print("📊 Dashboard: http://localhost:8001/docs")
        print("🔐 Default Admin: admin / admin123")
        print("👤 Default Manager: manager / manager123")
        print("💰 Default Cashier: cashier / cashier123")
        print("=" * 60 + "\n")
        
        start_server()
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
