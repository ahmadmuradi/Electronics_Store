"""
Comprehensive test suite for Enhanced Electronics Store Inventory System
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import os
from unittest.mock import Mock, patch, AsyncMock

# Import the application
from enhanced_main import app, get_db, Base, User, Product, Location, ProductLocation
from enhanced_main import create_access_token, get_password_hash
from ai_analytics import DemandForecaster, PriceOptimizer, AutoReorderSystem
from cloud_integrations import CloudBackupManager, EmailNotificationSystem

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_enhanced.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_token(test_db):
    """Create admin user and return auth token"""
    # Create admin user
    admin_user = User(
        username="testadmin",
        email="admin@test.com",
        full_name="Test Admin",
        role="admin",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    test_db.add(admin_user)
    test_db.commit()
    
    # Create token
    token = create_access_token(data={"sub": admin_user.username})
    return f"Bearer {token}"

@pytest.fixture
def manager_token(test_db):
    """Create manager user and return auth token"""
    manager_user = User(
        username="testmanager",
        email="manager@test.com",
        full_name="Test Manager",
        role="manager",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    test_db.add(manager_user)
    test_db.commit()
    
    token = create_access_token(data={"sub": manager_user.username})
    return f"Bearer {token}"

@pytest.fixture
def test_location(test_db):
    """Create test location"""
    location = Location(
        name="Test Store",
        address="123 Test St",
        is_active=True
    )
    test_db.add(location)
    test_db.commit()
    test_db.refresh(location)
    return location

@pytest.fixture
def test_product(test_db):
    """Create test product"""
    product = Product(
        name="Test iPhone",
        description="Test smartphone",
        price=999.99,
        cost=800.00,
        sku="TEST-IPH-001",
        reorder_level=10,
        reorder_quantity=50,
        requires_serial=True
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)
    return product

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "full_name": "New User",
            "role": "cashier",
            "password": "newpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "cashier"
    
    def test_login_user(self, client, test_db):
        """Test user login"""
        # Create user first
        user = User(
            username="logintest",
            email="login@test.com",
            full_name="Login Test",
            role="manager",
            hashed_password=get_password_hash("loginpass123"),
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        
        # Test login
        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "loginpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_invalid_login(self, client):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 401

class TestLocationManagement:
    """Test location management endpoints"""
    
    def test_create_location(self, client, admin_token):
        """Test creating a new location"""
        response = client.post(
            "/locations/",
            json={
                "name": "New Store",
                "address": "456 New St",
                "manager_id": None
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Store"
        assert data["is_active"] == True
    
    def test_get_locations(self, client, manager_token, test_location):
        """Test retrieving locations"""
        response = client.get(
            "/locations/",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(loc["name"] == "Test Store" for loc in data)

class TestProductManagement:
    """Test product management endpoints"""
    
    def test_create_product(self, client, admin_token):
        """Test creating a new product"""
        response = client.post(
            "/products/",
            json={
                "name": "Test Laptop",
                "description": "Gaming laptop",
                "price": 1499.99,
                "cost": 1200.00,
                "sku": "TEST-LAP-001",
                "reorder_level": 5,
                "reorder_quantity": 25,
                "requires_batch": True
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Laptop"
        assert data["requires_batch"] == True
    
    def test_get_products(self, client, manager_token, test_product):
        """Test retrieving products"""
        response = client.get(
            "/products/",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_product_locations(self, client, manager_token, test_product, test_location, test_db):
        """Test getting product stock by location"""
        # Add product to location
        product_location = ProductLocation(
            product_id=test_product.product_id,
            location_id=test_location.location_id,
            stock_quantity=100
        )
        test_db.add(product_location)
        test_db.commit()
        
        response = client.get(
            f"/products/{test_product.product_id}/locations",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["stock_quantity"] == 100

class TestInventoryManagement:
    """Test inventory management features"""
    
    def test_create_product_location(self, client, admin_token, test_product, test_location):
        """Test adding product to location"""
        response = client.post(
            "/product-locations/",
            json={
                "product_id": test_product.product_id,
                "location_id": test_location.location_id,
                "stock_quantity": 50
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stock_quantity"] == 50
    
    def test_update_stock(self, client, manager_token, test_product, test_location, test_db):
        """Test updating stock levels"""
        # Create product location first
        product_location = ProductLocation(
            product_id=test_product.product_id,
            location_id=test_location.location_id,
            stock_quantity=20
        )
        test_db.add(product_location)
        test_db.commit()
        
        # Update stock
        response = client.put(
            f"/product-locations/{test_product.product_id}/{test_location.location_id}/stock?quantity_change=10",
            json={"notes": "Stock adjustment test"},
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["new_stock_quantity"] == 30

class TestBatchSerialTracking:
    """Test batch and serial number tracking"""
    
    def test_create_batch_serial(self, client, admin_token, test_product, test_location):
        """Test creating batch/serial entry"""
        response = client.post(
            "/batch-serials/",
            json={
                "product_id": test_product.product_id,
                "location_id": test_location.location_id,
                "serial_number": "SN123456789",
                "batch_number": "BATCH001"
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["serial_number"] == "SN123456789"
        assert data["status"] == "available"
    
    def test_get_product_batch_serials(self, client, manager_token, test_product, test_location, test_db):
        """Test retrieving batch/serial numbers"""
        from enhanced_main import BatchSerial
        
        # Create batch/serial entry
        batch_serial = BatchSerial(
            product_id=test_product.product_id,
            location_id=test_location.location_id,
            serial_number="SN987654321",
            status="available"
        )
        test_db.add(batch_serial)
        test_db.commit()
        
        response = client.get(
            f"/products/{test_product.product_id}/batch-serials",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

class TestAIAnalytics:
    """Test AI analytics features"""
    
    @patch('ai_analytics.DemandForecaster.predict_demand')
    def test_demand_forecast(self, mock_predict, client, admin_token, test_product):
        """Test demand forecasting endpoint"""
        mock_predict.return_value = {
            "success": True,
            "product_id": test_product.product_id,
            "total_predicted_demand": 150.0,
            "average_daily_demand": 5.0,
            "predictions": []
        }
        
        response = client.get(
            f"/analytics/demand-forecast/{test_product.product_id}?days_ahead=30",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["total_predicted_demand"] == 150.0
    
    @patch('ai_analytics.PriceOptimizer.optimize_price')
    def test_price_optimization(self, mock_optimize, client, admin_token, test_product):
        """Test price optimization endpoint"""
        mock_optimize.return_value = {
            "success": True,
            "current_price": 999.99,
            "optimal_price": 1049.99,
            "profit_improvement_percent": 15.2
        }
        
        response = client.get(
            f"/analytics/price-optimization/{test_product.product_id}",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["optimal_price"] == 1049.99
    
    @patch('ai_analytics.AutoReorderSystem.generate_reorder_suggestions')
    def test_reorder_suggestions(self, mock_suggestions, client, admin_token):
        """Test reorder suggestions endpoint"""
        mock_suggestions.return_value = [
            {
                "product_id": 1,
                "product_name": "Test Product",
                "current_stock": 5,
                "reorder_level": 10,
                "suggested_order_quantity": 50,
                "priority": 80
            }
        ]
        
        response = client.get(
            "/analytics/reorder-suggestions",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["priority"] == 80

class TestCloudIntegrations:
    """Test cloud backup and integration features"""
    
    @patch('cloud_integrations.CloudBackupManager.create_database_backup')
    async def test_create_backup(self, mock_backup, client, admin_token):
        """Test database backup creation"""
        mock_backup.return_value = {
            "success": True,
            "timestamp": "20231201_120000",
            "tables_backed_up": 10,
            "total_records": 1000
        }
        
        response = client.post(
            "/cloud/backup/create",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "background" in data["message"]
    
    @patch('cloud_integrations.CloudBackupManager.list_backups')
    async def test_list_backups(self, mock_list, client, admin_token):
        """Test listing available backups"""
        mock_list.return_value = [
            {
                "filename": "backup_20231201_120000.json",
                "size": 1024000,
                "created": "2023-12-01T12:00:00",
                "location": "local"
            }
        ]
        
        response = client.get(
            "/cloud/backup/list",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        # Note: This will test the actual function, not the mock
        # since we're testing the endpoint, not the background task
    
    def test_quickbooks_auth_url(self, client, admin_token):
        """Test QuickBooks authorization URL generation"""
        with patch.dict(os.environ, {
            'QUICKBOOKS_CLIENT_ID': 'test_client_id',
            'QUICKBOOKS_CLIENT_SECRET': 'test_secret'
        }):
            response = client.get(
                "/integrations/quickbooks/auth-url",
                headers={"Authorization": admin_token}
            )
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data

class TestNotifications:
    """Test notification system"""
    
    @patch('cloud_integrations.EmailNotificationSystem.send_low_stock_alert')
    async def test_send_low_stock_alert(self, mock_send, client, admin_token):
        """Test sending low stock alert email"""
        mock_send.return_value = {"success": True, "recipients": ["manager@test.com"]}
        
        response = client.post(
            "/notifications/send-low-stock-alert?manager_email=manager@test.com",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "queued" in data["message"]
    
    @patch('cloud_integrations.EmailNotificationSystem.send_sales_report')
    async def test_send_sales_report(self, mock_send, client, admin_token):
        """Test sending sales report email"""
        mock_send.return_value = {"success": True, "recipients": ["admin@test.com"]}
        
        response = client.post(
            "/notifications/send-sales-report?recipient_email=admin@test.com",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

class TestReorderAlerts:
    """Test reorder alert system"""
    
    def test_get_reorder_alerts(self, client, admin_token, test_db):
        """Test retrieving reorder alerts"""
        from enhanced_main import ReorderAlert
        
        # Create test alert
        alert = ReorderAlert(
            product_id=1,
            location_id=1,
            current_stock=5,
            reorder_level=10,
            suggested_quantity=50,
            status="pending"
        )
        test_db.add(alert)
        test_db.commit()
        
        response = client.get(
            "/reorder-alerts/?status=pending",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_acknowledge_reorder_alert(self, client, admin_token, test_db):
        """Test acknowledging reorder alert"""
        from enhanced_main import ReorderAlert
        
        # Create test alert
        alert = ReorderAlert(
            product_id=1,
            location_id=1,
            current_stock=3,
            reorder_level=10,
            suggested_quantity=50,
            status="pending"
        )
        test_db.add(alert)
        test_db.commit()
        test_db.refresh(alert)
        
        response = client.put(
            f"/reorder-alerts/{alert.alert_id}/acknowledge",
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "acknowledged" in data["message"]

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_only_endpoint(self, client, manager_token):
        """Test that manager cannot access admin-only endpoints"""
        response = client.post(
            "/analytics/bulk-train-models",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 403
    
    def test_manager_access(self, client, manager_token):
        """Test that manager can access manager-level endpoints"""
        response = client.get(
            "/analytics/reorder-suggestions",
            headers={"Authorization": manager_token}
        )
        assert response.status_code == 200

class TestDataValidation:
    """Test input validation and error handling"""
    
    def test_invalid_product_data(self, client, admin_token):
        """Test creating product with invalid data"""
        response = client.post(
            "/products/",
            json={
                "name": "",  # Empty name should fail
                "price": -100,  # Negative price should fail
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 422  # Validation error
    
    def test_duplicate_sku(self, client, admin_token, test_product):
        """Test creating product with duplicate SKU"""
        response = client.post(
            "/products/",
            json={
                "name": "Another iPhone",
                "price": 899.99,
                "sku": test_product.sku  # Duplicate SKU
            },
            headers={"Authorization": admin_token}
        )
        assert response.status_code == 400

# Performance and Load Tests
class TestPerformance:
    """Test system performance under load"""
    
    def test_bulk_product_creation(self, client, admin_token):
        """Test creating multiple products"""
        products_created = 0
        for i in range(10):
            response = client.post(
                "/products/",
                json={
                    "name": f"Bulk Product {i}",
                    "price": 99.99 + i,
                    "sku": f"BULK-{i:03d}",
                    "reorder_level": 5,
                    "reorder_quantity": 25
                },
                headers={"Authorization": admin_token}
            )
            if response.status_code == 200:
                products_created += 1
        
        assert products_created == 10

# Integration Tests
class TestEndToEndWorkflows:
    """Test complete business workflows"""
    
    def test_complete_inventory_workflow(self, client, admin_token, test_db):
        """Test complete inventory management workflow"""
        # 1. Create location
        location_response = client.post(
            "/locations/",
            json={"name": "Workflow Store", "address": "123 Workflow St"},
            headers={"Authorization": admin_token}
        )
        assert location_response.status_code == 200
        location = location_response.json()
        
        # 2. Create product
        product_response = client.post(
            "/products/",
            json={
                "name": "Workflow Product",
                "price": 199.99,
                "cost": 150.00,
                "sku": "WF-001",
                "reorder_level": 10,
                "requires_serial": True
            },
            headers={"Authorization": admin_token}
        )
        assert product_response.status_code == 200
        product = product_response.json()
        
        # 3. Add product to location
        product_location_response = client.post(
            "/product-locations/",
            json={
                "product_id": product["product_id"],
                "location_id": location["location_id"],
                "stock_quantity": 25
            },
            headers={"Authorization": admin_token}
        )
        assert product_location_response.status_code == 200
        
        # 4. Add serial numbers
        for i in range(5):
            serial_response = client.post(
                "/batch-serials/",
                json={
                    "product_id": product["product_id"],
                    "location_id": location["location_id"],
                    "serial_number": f"WF{i:06d}"
                },
                headers={"Authorization": admin_token}
            )
            assert serial_response.status_code == 200
        
        # 5. Update stock (simulate sale)
        stock_update_response = client.put(
            f"/product-locations/{product['product_id']}/{location['location_id']}/stock?quantity_change=-15",
            json={"notes": "Sales transaction"},
            headers={"Authorization": admin_token}
        )
        assert stock_update_response.status_code == 200
        
        # 6. Check if reorder alert is triggered (stock should be 10, which equals reorder level)
        # This would be handled by background tasks in real scenario

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
