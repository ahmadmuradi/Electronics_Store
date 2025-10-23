import requests
import json

API_BASE = "http://localhost:8000"

# First, create a supplier
supplier_data = {
    "name": "Test Supplier",
    "contact_person": "John Doe",
    "phone": "123-456-7890",
    "email": "john@test.com",
    "address": "123 Test St"
}
response = requests.post(f"{API_BASE}/suppliers/", json=supplier_data)
if response.status_code == 200:
    supplier_id = response.json()["supplier_id"]
    print(f"Created supplier with ID: {supplier_id}")
else:
    print(f"Failed to create supplier: {response.status_code}")
    supplier_id = 1  # Assume ID 1 if fails

# Create a category
category_data = {"name": "Electronics"}
response = requests.post(f"{API_BASE}/categories/", json=category_data)
if response.status_code == 200:
    category_id = response.json()["category_id"]
    print(f"Created category with ID: {category_id}")
else:
    print(f"Failed to create category: {response.status_code}")
    category_id = 1  # Assume ID 1 if fails

# Create test products
products = [
    {
        "name": "iPhone 15",
        "description": "Latest iPhone model",
        "price": 999.99,
        "cost": 800.00,
        "stock_quantity": 10,
        "sku": "IPH15-001",
        "upc": "123456789012",
        "supplier_id": supplier_id,
        "category_id": category_id
    },
    {
        "name": "Dell Laptop",
        "description": "Gaming laptop",
        "price": 1499.99,
        "cost": 1200.00,
        "stock_quantity": 5,
        "sku": "DLL-LPT-001",
        "upc": "987654321098",
        "supplier_id": supplier_id,
        "category_id": category_id
    }
]

for product_data in products:
    response = requests.post(f"{API_BASE}/products/", json=product_data)
    if response.status_code == 200:
        print(f"Created product: {product_data['name']}")
    else:
        print(f"Failed to create product {product_data['name']}: {response.status_code} - {response.text}")

print("Test data added successfully. Refresh the Electron app to see inventory.")
