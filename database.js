// database.js - SQLite database manager for local data storage
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const { app } = require('electron');

class DatabaseManager {
    constructor() {
        // Create database in user data directory
        const userDataPath = app.getPath('userData');
        this.dbPath = path.join(userDataPath, 'inventory.db');
        this.db = null;
    }

    // Initialize database connection and create tables
    async initialize() {
        return new Promise((resolve, reject) => {
            this.db = new sqlite3.Database(this.dbPath, (err) => {
                if (err) {
                    console.error('Error opening database:', err);
                    reject(err);
                    return;
                }
                console.log('Connected to SQLite database at:', this.dbPath);
                this.createTables()
                    .then(() => resolve())
                    .catch(reject);
            });
        });
    }

    // Create necessary tables
    async createTables() {
        const tables = [
            // Products table
            `CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                cost REAL DEFAULT 0,
                stock_quantity INTEGER NOT NULL,
                min_stock_level INTEGER DEFAULT 10,
                sku TEXT UNIQUE,
                barcode TEXT UNIQUE,
                category TEXT,
                supplier_id INTEGER,
                tax_rate REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`,
            
            // Customers table
            `CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                loyalty_points INTEGER DEFAULT 0,
                total_spent REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`,
            
            // Suppliers table
            `CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                payment_terms TEXT,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`,
            
            // Product variants table
            `CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                variant_value TEXT NOT NULL,
                price_adjustment REAL DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                sku TEXT UNIQUE,
                barcode TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )`,
            
            // Purchase orders table
            `CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                order_number TEXT UNIQUE NOT NULL,
                order_date DATE NOT NULL,
                expected_date DATE,
                received_date DATE,
                status TEXT DEFAULT 'pending',
                subtotal REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )`,
            
            // Purchase order items table
            `CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                variant_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                received_quantity INTEGER DEFAULT 0,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (variant_id) REFERENCES product_variants (id)
            )`,
            
            // Sales table
            `CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                subtotal REAL NOT NULL,
                tax_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                payment_status TEXT DEFAULT 'completed',
                receipt_number TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )`,
            
            // Sale items table
            `CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )`,
            
            // Settings table for app configuration
            `CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )`
        ];

        for (const tableSQL of tables) {
            await this.runQuery(tableSQL);
        }

        // Insert default settings
        await this.insertDefaultSettings();
    }

    // Insert default application settings
    async insertDefaultSettings() {
        const defaultSettings = [
            { key: 'api_base_url', value: 'http://localhost:8000' },
            { key: 'low_stock_threshold', value: '10' },
            { key: 'currency_symbol', value: '$' },
            { key: 'sync_enabled', value: 'true' }
        ];

        for (const setting of defaultSettings) {
            await this.runQuery(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                [setting.key, setting.value]
            );
        }
    }

    // Generic query runner
    runQuery(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function(err) {
                if (err) {
                    console.error('Database query error:', err);
                    reject(err);
                } else {
                    resolve({ id: this.lastID, changes: this.changes });
                }
            });
        });
    }

    // Generic query getter
    getQuery(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.get(sql, params, (err, row) => {
                if (err) {
                    console.error('Database query error:', err);
                    reject(err);
                } else {
                    resolve(row);
                }
            });
        });
    }

    // Generic query all getter
    getAllQuery(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.all(sql, params, (err, rows) => {
                if (err) {
                    console.error('Database query error:', err);
                    reject(err);
                } else {
                    resolve(rows);
                }
            });
        });
    }

    // Product operations
    async addProduct(product) {
        const sql = `INSERT INTO products (name, description, price, stock_quantity, sku) 
                     VALUES (?, ?, ?, ?, ?)`;
        const params = [product.name, product.description, product.price, product.stock_quantity, product.sku];
        return await this.runQuery(sql, params);
    }

    async getProducts() {
        return await this.getAllQuery('SELECT * FROM products ORDER BY name');
    }

    async getProduct(id) {
        return await this.getQuery('SELECT * FROM products WHERE id = ?', [id]);
    }

    async updateProduct(id, product) {
        const sql = `UPDATE products 
                     SET name = ?, price = ?, stock_quantity = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?`;
        const params = [product.name, product.price, product.stock_quantity, id];
        return await this.runQuery(sql, params);
    }

    async deleteProduct(id) {
        return await this.runQuery('DELETE FROM products WHERE id = ?', [id]);
    }

    async getProductByBarcode(barcode) {
        return await this.getQuery('SELECT * FROM products WHERE barcode = ?', [barcode]);
    }

    // Customer operations
    async addCustomer(customer) {
        const sql = `INSERT INTO customers (name, email, phone, address, city, postal_code) 
                     VALUES (?, ?, ?, ?, ?, ?)`;
        const params = [customer.name, customer.email, customer.phone, customer.address, customer.city, customer.postal_code];
        return await this.runQuery(sql, params);
    }

    async getCustomers() {
        return await this.getAllQuery('SELECT * FROM customers ORDER BY name');
    }

    async getCustomer(id) {
        return await this.getQuery('SELECT * FROM customers WHERE id = ?', [id]);
    }

    async updateCustomer(id, customer) {
        const sql = `UPDATE customers 
                     SET name = ?, email = ?, phone = ?, address = ?, city = ?, postal_code = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?`;
        const params = [customer.name, customer.email, customer.phone, customer.address, customer.city, customer.postal_code, id];
        return await this.runQuery(sql, params);
    }

    async deleteCustomer(id) {
        return await this.runQuery('DELETE FROM customers WHERE id = ?', [id]);
    }

    async updateCustomerLoyalty(customerId, pointsToAdd, amountSpent) {
        const sql = `UPDATE customers 
                     SET loyalty_points = loyalty_points + ?, total_spent = total_spent + ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?`;
        return await this.runQuery(sql, [pointsToAdd, amountSpent, customerId]);
    }

    // Supplier operations
    async addSupplier(supplier) {
        const sql = `INSERT INTO suppliers (name, contact_person, email, phone, address, city, country, payment_terms, notes) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`;
        const params = [supplier.name, supplier.contact_person, supplier.email, supplier.phone, 
                       supplier.address, supplier.city, supplier.country, supplier.payment_terms, supplier.notes];
        return await this.runQuery(sql, params);
    }

    async getSuppliers() {
        return await this.getAllQuery('SELECT * FROM suppliers WHERE is_active = 1 ORDER BY name');
    }

    async getSupplier(id) {
        return await this.getQuery('SELECT * FROM suppliers WHERE id = ?', [id]);
    }

    async updateSupplier(id, supplier) {
        const sql = `UPDATE suppliers 
                     SET name = ?, contact_person = ?, email = ?, phone = ?, address = ?, city = ?, 
                         country = ?, payment_terms = ?, notes = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?`;
        const params = [supplier.name, supplier.contact_person, supplier.email, supplier.phone,
                       supplier.address, supplier.city, supplier.country, supplier.payment_terms, supplier.notes, id];
        return await this.runQuery(sql, params);
    }

    async deleteSupplier(id) {
        return await this.runQuery('UPDATE suppliers SET is_active = 0 WHERE id = ?', [id]);
    }

    // Product variant operations
    async addProductVariant(variant) {
        const sql = `INSERT INTO product_variants (product_id, variant_name, variant_value, price_adjustment, stock_quantity, sku, barcode) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)`;
        const params = [variant.product_id, variant.variant_name, variant.variant_value, 
                       variant.price_adjustment || 0, variant.stock_quantity || 0, variant.sku, variant.barcode];
        return await this.runQuery(sql, params);
    }

    async getProductVariants(productId) {
        return await this.getAllQuery('SELECT * FROM product_variants WHERE product_id = ?', [productId]);
    }

    async getAllProductVariants() {
        return await this.getAllQuery(`
            SELECT pv.*, p.name as product_name 
            FROM product_variants pv 
            JOIN products p ON pv.product_id = p.id 
            ORDER BY p.name, pv.variant_name
        `);
    }

    async updateProductVariant(id, variant) {
        const sql = `UPDATE product_variants 
                     SET variant_name = ?, variant_value = ?, price_adjustment = ?, stock_quantity = ?, sku = ?, barcode = ?
                     WHERE id = ?`;
        const params = [variant.variant_name, variant.variant_value, variant.price_adjustment, 
                       variant.stock_quantity, variant.sku, variant.barcode, id];
        return await this.runQuery(sql, params);
    }

    async deleteProductVariant(id) {
        return await this.runQuery('DELETE FROM product_variants WHERE id = ?', [id]);
    }

    // Purchase order operations
    async addPurchaseOrder(order) {
        const orderNumber = `PO-${Date.now()}-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
        
        const orderResult = await this.runQuery(
            `INSERT INTO purchase_orders (supplier_id, order_number, order_date, expected_date, subtotal, tax_amount, total_amount, notes) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [order.supplier_id, orderNumber, order.order_date, order.expected_date, 
             order.subtotal, order.tax_amount || 0, order.total_amount, order.notes]
        );

        const orderId = orderResult.id;

        // Add order items
        for (const item of order.items) {
            await this.runQuery(
                'INSERT INTO purchase_order_items (purchase_order_id, product_id, variant_id, quantity, unit_cost, total_cost) VALUES (?, ?, ?, ?, ?, ?)',
                [orderId, item.product_id, item.variant_id, item.quantity, item.unit_cost, item.total_cost]
            );
        }

        return { ...orderResult, order_number: orderNumber };
    }

    async getPurchaseOrders() {
        return await this.getAllQuery(`
            SELECT po.*, s.name as supplier_name, COUNT(poi.id) as item_count
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN purchase_order_items poi ON po.id = poi.purchase_order_id
            GROUP BY po.id
            ORDER BY po.created_at DESC
        `);
    }

    async receivePurchaseOrder(orderId, receivedItems) {
        // Update received quantities
        for (const item of receivedItems) {
            await this.runQuery(
                'UPDATE purchase_order_items SET received_quantity = ? WHERE id = ?',
                [item.received_quantity, item.id]
            );

            // Update product stock
            if (item.variant_id) {
                await this.runQuery(
                    'UPDATE product_variants SET stock_quantity = stock_quantity + ? WHERE id = ?',
                    [item.received_quantity, item.variant_id]
                );
            } else {
                await this.runQuery(
                    'UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?',
                    [item.received_quantity, item.product_id]
                );
            }
        }

        // Update order status
        await this.runQuery(
            'UPDATE purchase_orders SET status = ?, received_date = CURRENT_DATE WHERE id = ?',
            ['received', orderId]
        );
    }

    // Enhanced sale operations
    async addSale(sale) {
        const { v4: uuidv4 } = require('uuid');
        const receiptNumber = `RCP-${Date.now()}-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
        
        const saleResult = await this.runQuery(
            `INSERT INTO sales (customer_id, subtotal, tax_amount, discount_amount, total_amount, payment_method, receipt_number) 
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            [sale.customer_id, sale.subtotal, sale.tax_amount || 0, sale.discount_amount || 0, 
             sale.total_amount, sale.payment_method || 'cash', receiptNumber]
        );

        const saleId = saleResult.id;

        // Add sale items
        for (const item of sale.items) {
            await this.runQuery(
                'INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?)',
                [saleId, item.product_id, item.quantity, item.unit_price, item.total_price]
            );

            // Update product stock
            await this.runQuery(
                'UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?',
                [item.quantity, item.product_id]
            );
        }

        // Update customer loyalty points if customer exists
        if (sale.customer_id) {
            const loyaltyPoints = Math.floor(sale.total_amount); // 1 point per dollar
            await this.updateCustomerLoyalty(sale.customer_id, loyaltyPoints, sale.total_amount);
        }

        return { ...saleResult, receipt_number: receiptNumber };
    }

    async getSaleByReceiptNumber(receiptNumber) {
        const sale = await this.getQuery('SELECT * FROM sales WHERE receipt_number = ?', [receiptNumber]);
        if (sale) {
            sale.items = await this.getAllQuery(`
                SELECT si.*, p.name as product_name, p.sku
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            `, [sale.id]);
            
            if (sale.customer_id) {
                sale.customer = await this.getCustomer(sale.customer_id);
            }
        }
        return sale;
    }

    async getSales() {
        const sales = await this.getAllQuery(`
            SELECT s.*, 
                   COUNT(si.id) as item_count,
                   GROUP_CONCAT(p.name) as product_names
            FROM sales s
            LEFT JOIN sale_items si ON s.id = si.sale_id
            LEFT JOIN products p ON si.product_id = p.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        `);

        // Get detailed items for each sale
        for (const sale of sales) {
            sale.items = await this.getAllQuery(`
                SELECT si.*, p.name as product_name
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            `, [sale.id]);
        }

        return sales;
    }

    // Analytics and reporting
    async getTopSellingProducts(limit = 5) {
        return await this.getAllQuery(`
            SELECT p.name, p.id, SUM(si.quantity) as total_sold, SUM(si.total_price) as total_revenue
            FROM products p
            JOIN sale_items si ON p.id = si.product_id
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT ?
        `, [limit]);
    }

    async getLowStockProducts(threshold = 10) {
        return await this.getAllQuery(
            'SELECT * FROM products WHERE stock_quantity <= ? ORDER BY stock_quantity ASC',
            [threshold]
        );
    }

    async getSalesReport(startDate, endDate) {
        const sql = `
            SELECT 
                DATE(s.created_at) as sale_date,
                COUNT(s.id) as total_sales,
                SUM(s.total_amount) as total_revenue,
                AVG(s.total_amount) as avg_sale_amount
            FROM sales s
            WHERE DATE(s.created_at) BETWEEN ? AND ?
            GROUP BY DATE(s.created_at)
            ORDER BY sale_date DESC
        `;
        return await this.getAllQuery(sql, [startDate, endDate]);
    }

    // Settings operations
    async getSetting(key) {
        const result = await this.getQuery('SELECT value FROM settings WHERE key = ?', [key]);
        return result ? result.value : null;
    }

    async setSetting(key, value) {
        return await this.runQuery(
            'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            [key, value]
        );
    }

    // Export/Import operations
    async exportProductsToCSV() {
        const products = await this.getAllQuery(`
            SELECT p.*, s.name as supplier_name 
            FROM products p 
            LEFT JOIN suppliers s ON p.supplier_id = s.id 
            ORDER BY p.name
        `);
        return products;
    }

    async exportSalesToCSV(startDate, endDate) {
        const sales = await this.getAllQuery(`
            SELECT s.*, c.name as customer_name, c.email as customer_email
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE DATE(s.created_at) BETWEEN ? AND ?
            ORDER BY s.created_at DESC
        `, [startDate, endDate]);

        // Get detailed sales with items
        for (const sale of sales) {
            sale.items = await this.getAllQuery(`
                SELECT si.*, p.name as product_name, p.sku
                FROM sale_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.sale_id = ?
            `, [sale.id]);
        }

        return sales;
    }

    async importProductsFromCSV(products) {
        const results = { success: 0, errors: [] };
        
        for (const product of products) {
            try {
                await this.addProduct({
                    name: product.name,
                    description: product.description || '',
                    price: parseFloat(product.price),
                    cost: parseFloat(product.cost) || 0,
                    stock_quantity: parseInt(product.stock_quantity),
                    min_stock_level: parseInt(product.min_stock_level) || 10,
                    sku: product.sku || '',
                    barcode: product.barcode || '',
                    category: product.category || '',
                    supplier_id: product.supplier_id || null
                });
                results.success++;
            } catch (error) {
                results.errors.push(`Row ${products.indexOf(product) + 1}: ${error.message}`);
            }
        }
        
        return results;
    }

    // Profit analysis operations
    async getProfitAnalysis(startDate, endDate) {
        const profitData = await this.getAllQuery(`
            SELECT 
                p.id,
                p.name,
                p.category,
                p.cost,
                p.price,
                (p.price - p.cost) as profit_per_unit,
                CASE WHEN p.cost > 0 THEN ((p.price - p.cost) / p.cost * 100) ELSE 0 END as profit_margin_percent,
                COALESCE(SUM(si.quantity), 0) as units_sold,
                COALESCE(SUM(si.total_price), 0) as total_revenue,
                COALESCE(SUM(si.quantity * p.cost), 0) as total_cost,
                COALESCE(SUM(si.total_price - (si.quantity * p.cost)), 0) as total_profit
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND DATE(s.created_at) BETWEEN ? AND ?
            GROUP BY p.id, p.name, p.category, p.cost, p.price
            ORDER BY total_profit DESC
        `, [startDate, endDate]);

        return profitData;
    }

    async getCategoryProfitAnalysis(startDate, endDate) {
        return await this.getAllQuery(`
            SELECT 
                p.category,
                COUNT(DISTINCT p.id) as product_count,
                COALESCE(SUM(si.quantity), 0) as units_sold,
                COALESCE(SUM(si.total_price), 0) as total_revenue,
                COALESCE(SUM(si.quantity * p.cost), 0) as total_cost,
                COALESCE(SUM(si.total_price - (si.quantity * p.cost)), 0) as total_profit,
                CASE 
                    WHEN SUM(si.total_price) > 0 
                    THEN (SUM(si.total_price - (si.quantity * p.cost)) / SUM(si.total_price) * 100)
                    ELSE 0 
                END as profit_margin_percent
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND DATE(s.created_at) BETWEEN ? AND ?
            WHERE p.category IS NOT NULL AND p.category != ''
            GROUP BY p.category
            ORDER BY total_profit DESC
        `, [startDate, endDate]);
    }

    async getInventoryTurnoverAnalysis() {
        return await this.getAllQuery(`
            SELECT 
                p.id,
                p.name,
                p.category,
                p.stock_quantity,
                p.cost * p.stock_quantity as inventory_value,
                COALESCE(SUM(si.quantity), 0) as total_sold_last_30_days,
                CASE 
                    WHEN p.stock_quantity > 0 AND SUM(si.quantity) > 0
                    THEN (SUM(si.quantity) / p.stock_quantity)
                    ELSE 0 
                END as turnover_ratio,
                CASE 
                    WHEN SUM(si.quantity) > 0 
                    THEN (30.0 / (SUM(si.quantity) / p.stock_quantity))
                    ELSE 999 
                END as days_to_sell_inventory
            FROM products p
            LEFT JOIN sale_items si ON p.id = si.product_id
            LEFT JOIN sales s ON si.sale_id = s.id AND s.created_at >= DATE('now', '-30 days')
            GROUP BY p.id, p.name, p.category, p.stock_quantity, p.cost
            HAVING p.stock_quantity > 0
            ORDER BY turnover_ratio DESC
        `);
    }

    // Reorder point analysis
    async getReorderPointAnalysis() {
        return await this.getAllQuery(`
            SELECT 
                p.id,
                p.name,
                p.stock_quantity,
                p.min_stock_level,
                COALESCE(AVG(daily_sales.daily_quantity), 0) as avg_daily_sales,
                CASE 
                    WHEN AVG(daily_sales.daily_quantity) > 0 
                    THEN (p.stock_quantity / AVG(daily_sales.daily_quantity))
                    ELSE 999 
                END as days_of_stock_remaining,
                CASE 
                    WHEN p.stock_quantity <= p.min_stock_level THEN 'REORDER_NOW'
                    WHEN AVG(daily_sales.daily_quantity) > 0 AND (p.stock_quantity / AVG(daily_sales.daily_quantity)) <= 7 THEN 'REORDER_SOON'
                    ELSE 'OK'
                END as reorder_status
            FROM products p
            LEFT JOIN (
                SELECT 
                    si.product_id,
                    DATE(s.created_at) as sale_date,
                    SUM(si.quantity) as daily_quantity
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE s.created_at >= DATE('now', '-30 days')
                GROUP BY si.product_id, DATE(s.created_at)
            ) daily_sales ON p.id = daily_sales.product_id
            GROUP BY p.id, p.name, p.stock_quantity, p.min_stock_level
            ORDER BY 
                CASE 
                    WHEN p.stock_quantity <= p.min_stock_level THEN 1
                    WHEN AVG(daily_sales.daily_quantity) > 0 AND (p.stock_quantity / AVG(daily_sales.daily_quantity)) <= 7 THEN 2
                    ELSE 3
                END,
                p.stock_quantity ASC
        `);
    }

    // Close database connection
    close() {
        if (this.db) {
            this.db.close((err) => {
                if (err) {
                    console.error('Error closing database:', err);
                } else {
                    console.log('Database connection closed.');
                }
            });
        }
    }
}

module.exports = DatabaseManager;
