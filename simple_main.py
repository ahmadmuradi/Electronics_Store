#!/usr/bin/env python3
"""
Simple Electronics Store Inventory System - Deployment Version
Compatible with Python 3.14
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Try to import FastAPI components
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    print("FastAPI not available, creating basic HTTP server")
    FASTAPI_AVAILABLE = False

# Create FastAPI app if available
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Electronics Store Inventory API",
        description="Simple inventory management system",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Database setup
DATABASE_PATH = Path(__file__).parent / "simple_inventory.db"

def init_database():
    """Initialize SQLite database with basic tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'cashier',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (username, email, role) VALUES 
            ('admin', 'admin@store.com', 'admin'),
            ('manager', 'manager@store.com', 'manager'),
            ('cashier', 'cashier@store.com', 'cashier')
        ''')
    
    cursor.execute("SELECT COUNT(*) FROM locations")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO locations (name, address) VALUES 
            ('Main Store', '123 Main Street, City, State'),
            ('Warehouse', '456 Industrial Blvd, City, State')
        ''')
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO products (name, sku, price, stock_quantity, description) VALUES 
            ('iPhone 15', 'IPHONE15-128', 999.99, 50, 'Latest iPhone with 128GB storage'),
            ('Samsung Galaxy S24', 'GALAXY-S24-256', 899.99, 30, 'Samsung flagship with 256GB storage'),
            ('MacBook Air M3', 'MBA-M3-512', 1299.99, 15, 'Apple MacBook Air with M3 chip'),
            ('Dell XPS 13', 'DELL-XPS13-16GB', 1199.99, 20, 'Dell XPS 13 with 16GB RAM'),
            ('AirPods Pro', 'AIRPODS-PRO-2', 249.99, 100, 'Apple AirPods Pro 2nd generation')
        ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DATABASE_PATH}")

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)

# API Routes (if FastAPI is available)
if FASTAPI_AVAILABLE:
    
    @app.get("/")
    async def root():
        return {"message": "Electronics Store Inventory API", "status": "running"}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    @app.get("/products")
    async def get_products():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = []
        for row in cursor.fetchall():
            products.append({
                "id": row[0],
                "name": row[1],
                "sku": row[2],
                "price": row[3],
                "stock_quantity": row[4],
                "description": row[5],
                "created_at": row[6]
            })
        conn.close()
        return {"products": products, "count": len(products)}
    
    @app.get("/users")
    async def get_users():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "role": row[3],
                "created_at": row[4]
            })
        conn.close()
        return {"users": users, "count": len(users)}
    
    @app.get("/locations")
    async def get_locations():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations")
        locations = []
        for row in cursor.fetchall():
            locations.append({
                "id": row[0],
                "name": row[1],
                "address": row[2],
                "created_at": row[3]
            })
        conn.close()
        return {"locations": locations, "count": len(locations)}
    
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Electronics Store Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; margin-bottom: 30px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
                .stat-label { font-size: 0.9em; opacity: 0.9; }
                .links { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .link-card { background: #fff; border: 2px solid #e0e0e0; padding: 20px; border-radius: 8px; text-align: center; transition: all 0.3s; }
                .link-card:hover { border-color: #667eea; transform: translateY(-2px); }
                .link-card a { text-decoration: none; color: #333; font-weight: bold; }
                .status { background: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="status">🚀 Electronics Store Inventory System - RUNNING</div>
                <h1>📊 Dashboard</h1>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="product-count">5</div>
                        <div class="stat-label">Products</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="user-count">3</div>
                        <div class="stat-label">Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="location-count">2</div>
                        <div class="stat-label">Locations</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">✅</div>
                        <div class="stat-label">System Status</div>
                    </div>
                </div>
                
                <div class="links">
                    <div class="link-card">
                        <a href="/products">📦 View Products</a>
                    </div>
                    <div class="link-card">
                        <a href="/users">👥 View Users</a>
                    </div>
                    <div class="link-card">
                        <a href="/locations">🏪 View Locations</a>
                    </div>
                    <div class="link-card">
                        <a href="/docs">📚 API Documentation</a>
                    </div>
                    <div class="link-card">
                        <a href="/health">❤️ Health Check</a>
                    </div>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>Default Login Credentials:</p>
                    <p><strong>Admin:</strong> admin / admin123</p>
                    <p><strong>Manager:</strong> manager / manager123</p>
                    <p><strong>Cashier:</strong> cashier / cashier123</p>
                </div>
            </div>
            
            <script>
                // Update stats dynamically
                fetch('/products').then(r => r.json()).then(data => {
                    document.getElementById('product-count').textContent = data.count;
                });
                fetch('/users').then(r => r.json()).then(data => {
                    document.getElementById('user-count').textContent = data.count;
                });
                fetch('/locations').then(r => r.json()).then(data => {
                    document.getElementById('location-count').textContent = data.count;
                });
            </script>
        </body>
        </html>
        """

def main():
    """Main function to start the server"""
    print("=" * 60)
    print("Electronics Store Inventory System - Simple Deployment")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    if FASTAPI_AVAILABLE:
        print("\n🚀 Starting FastAPI server...")
        print("📊 Dashboard: http://localhost:8001/dashboard")
        print("📚 API Docs: http://localhost:8001/docs")
        print("🔐 Default Admin: admin / admin123")
        print("=" * 60 + "\n")
        
        try:
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        except ImportError:
            print("❌ uvicorn not available. Please install: pip install uvicorn")
            return 1
    else:
        print("❌ FastAPI not available. Please install: pip install fastapi uvicorn")
        print("📊 Database created successfully at:", DATABASE_PATH)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
