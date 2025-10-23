import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_product():
    response = client.post("/products/", json={
        "name": "Test Product",
        "price": 10.0,
        "stock_quantity": 100,
        "sku": "TEST123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["stock_quantity"] == 100

def test_read_products():
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_supplier():
    response = client.post("/suppliers/", json={
        "name": "Test Supplier",
        "contact_person": "John Doe",
        "phone": "123-456-7890",
        "email": "john@test.com",
        "address": "123 Test St"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Supplier"

def test_create_sale():
    # First, create a product if not exists
    client.post("/products/", json={
        "name": "Sale Product",
        "price": 20.0,
        "stock_quantity": 50,
        "sku": "SALE123"
    })
    response = client.post("/sales/", json={
        "customer_id": None,
        "items": [
            {"product_id": 1, "quantity": 2, "price": 20.0}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 40.0

def test_insufficient_stock_sale():
    response = client.post("/sales/", json={
        "customer_id": None,
        "items": [
            {"product_id": 1, "quantity": 1000, "price": 20.0}  # Assuming low stock
        ]
    })
    assert response.status_code == 400

def test_update_stock():
    response = client.put("/inventory/update_stock/1?quantity_change=10")
    assert response.status_code == 200
    data = response.json()
    assert "new_stock_quantity" in data

def test_create_purchase_order():
    # Create supplier first
    client.post("/suppliers/", json={
        "name": "PO Supplier",
        "contact_person": "Jane Doe",
        "phone": "098-765-4321",
        "email": "jane@test.com",
        "address": "456 PO St"
    })
    response = client.post("/purchase_orders/", json={
        "supplier_id": 1,
        "items": [
            {"product_id": 1, "quantity": 10, "unit_cost": 15.0}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == 150.0
