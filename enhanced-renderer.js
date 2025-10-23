// Enhanced renderer.js with multi-location, batch/serial tracking, and notifications

// Global state management
const AppState = {
    currentUser: null,
    currentLocation: null,
    locations: [],
    products: [],
    reorderAlerts: [],
    isOnline: navigator.onLine,
    authToken: localStorage.getItem('authToken')
};

// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:8001',
    TIMEOUT: 10000
};

// Utility Functions
class NotificationManager {
    static show(message, type = 'success', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type} fade-in`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            animation: slideIn 0.3s ease-out;
        `;
        
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        
        notification.style.background = colors[type] || colors.info;
        if (type === 'warning') notification.style.color = '#212529';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
    
    static getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }
}

class APIClient {
    static async request(endpoint, options = {}) {
        const url = `${API_CONFIG.BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(AppState.authToken && { 'Authorization': `Bearer ${AppState.authToken}` })
            },
            timeout: API_CONFIG.TIMEOUT
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }
    
    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }
    
    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

class AuthManager {
    static async login(username, password) {
        try {
            const response = await APIClient.post('/auth/login', { username, password });
            AppState.authToken = response.access_token;
            AppState.currentUser = response.user;
            localStorage.setItem('authToken', response.access_token);
            localStorage.setItem('currentUser', JSON.stringify(response.user));
            return response;
        } catch (error) {
            throw new Error(`Login failed: ${error.message}`);
        }
    }
    
    static logout() {
        AppState.authToken = null;
        AppState.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        window.location.reload();
    }
    
    static isAuthenticated() {
        return !!AppState.authToken;
    }
    
    static hasRole(roles) {
        if (!AppState.currentUser) return false;
        return roles.includes(AppState.currentUser.role);
    }
}

class LocationManager {
    static async loadLocations() {
        try {
            AppState.locations = await APIClient.get('/locations/');
            this.renderLocationSelector();
            return AppState.locations;
        } catch (error) {
            NotificationManager.show(`Failed to load locations: ${error.message}`, 'error');
            return [];
        }
    }
    
    static renderLocationSelector() {
        const selector = document.getElementById('location-selector');
        if (!selector) return;
        
        selector.innerHTML = `
            <select id="current-location" onchange="LocationManager.setCurrentLocation(this.value)">
                <option value="">Select Location</option>
                ${AppState.locations.map(loc => 
                    `<option value="${loc.location_id}" ${AppState.currentLocation?.location_id === loc.location_id ? 'selected' : ''}>
                        ${loc.name}
                    </option>`
                ).join('')}
            </select>
        `;
    }
    
    static setCurrentLocation(locationId) {
        AppState.currentLocation = AppState.locations.find(loc => loc.location_id == locationId);
        localStorage.setItem('currentLocation', JSON.stringify(AppState.currentLocation));
        InventoryManager.loadInventory();
        NotificationManager.show(`Switched to ${AppState.currentLocation?.name || 'All Locations'}`, 'info');
    }
}

class InventoryManager {
    static async loadInventory() {
        try {
            const products = await APIClient.get('/products/');
            AppState.products = products;
            
            // Load location-specific stock if location is selected
            if (AppState.currentLocation) {
                for (let product of products) {
                    try {
                        const locations = await APIClient.get(`/products/${product.product_id}/locations`);
                        const currentLocationStock = locations.find(loc => loc.location_id === AppState.currentLocation.location_id);
                        product.current_stock = currentLocationStock?.stock_quantity || 0;
                        product.reserved_stock = currentLocationStock?.reserved_quantity || 0;
                    } catch (error) {
                        product.current_stock = 0;
                        product.reserved_stock = 0;
                    }
                }
            }
            
            this.renderInventory();
            return products;
        } catch (error) {
            NotificationManager.show(`Failed to load inventory: ${error.message}`, 'error');
            return [];
        }
    }
    
    static renderInventory() {
        const container = document.getElementById('inventory-display');
        if (!container) return;
        
        if (AppState.products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Products Found</h3>
                    <p>Add your first product to get started!</p>
                </div>
            `;
            return;
        }
        
        const locationInfo = AppState.currentLocation ? 
            `<div class="location-info">Showing inventory for: <strong>${AppState.currentLocation.name}</strong></div>` : 
            '<div class="location-info">Showing inventory for: <strong>All Locations</strong></div>';
        
        container.innerHTML = `
            ${locationInfo}
            <div class="inventory-grid">
                ${AppState.products.map(product => this.renderProductCard(product)).join('')}
            </div>
        `;
    }
    
    static renderProductCard(product) {
        const stock = AppState.currentLocation ? product.current_stock : product.stock_quantity;
        const reserved = AppState.currentLocation ? product.reserved_stock : 0;
        const available = stock - reserved;
        
        const stockStatus = stock <= product.reorder_level ? 'critical' : stock <= (product.reorder_level * 2) ? 'low' : 'good';
        const stockColor = stockStatus === 'critical' ? '#dc3545' : stockStatus === 'low' ? '#ffc107' : '#28a745';
        
        return `
            <div class="product-card ${stockStatus}-stock">
                <div class="product-header">
                    <h4 class="product-name">${product.name}</h4>
                    <div class="product-sku">SKU: ${product.sku || 'N/A'}</div>
                </div>
                
                <div class="product-details">
                    <div class="price-info">
                        <span class="price">$${parseFloat(product.price).toFixed(2)}</span>
                        ${product.cost ? `<span class="cost">Cost: $${parseFloat(product.cost).toFixed(2)}</span>` : ''}
                    </div>
                    
                    <div class="stock-info" style="color: ${stockColor}">
                        <div class="stock-main">
                            <strong>Stock: ${stock}</strong>
                            ${reserved > 0 ? `<span class="reserved">(${reserved} reserved)</span>` : ''}
                        </div>
                        <div class="stock-available">Available: ${available}</div>
                        <div class="reorder-level">Reorder at: ${product.reorder_level}</div>
                    </div>
                    
                    ${product.requires_serial || product.requires_batch ? `
                        <div class="tracking-info">
                            ${product.requires_serial ? '<span class="badge">Serial Tracked</span>' : ''}
                            ${product.requires_batch ? '<span class="badge">Batch Tracked</span>' : ''}
                        </div>
                    ` : ''}
                </div>
                
                <div class="product-actions">
                    <button onclick="InventoryManager.showStockAdjustment(${product.product_id})" class="btn-primary">
                        Adjust Stock
                    </button>
                    ${product.requires_serial || product.requires_batch ? `
                        <button onclick="BatchSerialManager.showBatchSerial(${product.product_id})" class="btn-secondary">
                            Batch/Serial
                        </button>
                    ` : ''}
                    ${AuthManager.hasRole(['admin', 'manager']) ? `
                        <button onclick="InventoryManager.editProduct(${product.product_id})" class="btn-secondary">
                            Edit
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    static showStockAdjustment(productId) {
        const product = AppState.products.find(p => p.product_id === productId);
        if (!product) return;
        
        if (!AppState.currentLocation) {
            NotificationManager.show('Please select a location first', 'warning');
            return;
        }
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Adjust Stock - ${product.name}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                
                <div class="modal-body">
                    <div class="current-stock-info">
                        <p><strong>Current Stock:</strong> ${product.current_stock || 0}</p>
                        <p><strong>Location:</strong> ${AppState.currentLocation.name}</p>
                    </div>
                    
                    <form id="stock-adjustment-form">
                        <div class="form-group">
                            <label>Adjustment Type:</label>
                            <select id="adjustment-type" onchange="InventoryManager.updateAdjustmentForm()">
                                <option value="add">Add Stock (Receipt)</option>
                                <option value="remove">Remove Stock</option>
                                <option value="set">Set Exact Amount</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label id="quantity-label">Quantity to Add:</label>
                            <input type="number" id="quantity" min="1" required>
                        </div>
                        
                        <div class="form-group">
                            <label>Notes:</label>
                            <textarea id="notes" placeholder="Reason for adjustment..."></textarea>
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="btn-primary">Apply Adjustment</button>
                            <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        document.getElementById('stock-adjustment-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.applyStockAdjustment(productId);
        });
    }
    
    static updateAdjustmentForm() {
        const type = document.getElementById('adjustment-type').value;
        const label = document.getElementById('quantity-label');
        const input = document.getElementById('quantity');
        
        switch (type) {
            case 'add':
                label.textContent = 'Quantity to Add:';
                input.min = '1';
                break;
            case 'remove':
                label.textContent = 'Quantity to Remove:';
                input.min = '1';
                break;
            case 'set':
                label.textContent = 'New Stock Level:';
                input.min = '0';
                break;
        }
    }
    
    static async applyStockAdjustment(productId) {
        const type = document.getElementById('adjustment-type').value;
        const quantity = parseInt(document.getElementById('quantity').value);
        const notes = document.getElementById('notes').value;
        
        if (!AppState.currentLocation) {
            NotificationManager.show('No location selected', 'error');
            return;
        }
        
        const product = AppState.products.find(p => p.product_id === productId);
        let quantityChange;
        
        switch (type) {
            case 'add':
                quantityChange = quantity;
                break;
            case 'remove':
                quantityChange = -quantity;
                break;
            case 'set':
                quantityChange = quantity - (product.current_stock || 0);
                break;
        }
        
        try {
            const response = await APIClient.put(
                `/product-locations/${productId}/${AppState.currentLocation.location_id}/stock?quantity_change=${quantityChange}`,
                { notes }
            );
            
            NotificationManager.show('Stock updated successfully!', 'success');
            document.querySelector('.modal').remove();
            await this.loadInventory();
            
        } catch (error) {
            NotificationManager.show(`Failed to update stock: ${error.message}`, 'error');
        }
    }
}

class BatchSerialManager {
    static showBatchSerial(productId) {
        const product = AppState.products.find(p => p.product_id === productId);
        if (!product) return;
        
        const modal = document.createElement('div');
        modal.className = 'modal large';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Batch/Serial Management - ${product.name}</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                
                <div class="modal-body">
                    <div class="tabs">
                        <button class="tab-button active" onclick="BatchSerialManager.switchTab('list')">Current Items</button>
                        <button class="tab-button" onclick="BatchSerialManager.switchTab('add')">Add New</button>
                    </div>
                    
                    <div id="batch-serial-list" class="tab-content active">
                        <div class="loading">Loading batch/serial data...</div>
                    </div>
                    
                    <div id="batch-serial-add" class="tab-content">
                        <form id="batch-serial-form">
                            ${product.requires_batch ? `
                                <div class="form-group">
                                    <label>Batch Number:</label>
                                    <input type="text" id="batch-number" required>
                                </div>
                            ` : ''}
                            
                            ${product.requires_serial ? `
                                <div class="form-group">
                                    <label>Serial Number:</label>
                                    <input type="text" id="serial-number" required>
                                </div>
                            ` : ''}
                            
                            <div class="form-group">
                                <label>Expiry Date (optional):</label>
                                <input type="date" id="expiry-date">
                            </div>
                            
                            <div class="form-actions">
                                <button type="submit" class="btn-primary">Add Item</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.loadBatchSerialData(productId);
        
        document.getElementById('batch-serial-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.addBatchSerial(productId);
        });
    }
    
    static switchTab(tabName) {
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        document.querySelector(`[onclick="BatchSerialManager.switchTab('${tabName}')"]`).classList.add('active');
        document.getElementById(`batch-serial-${tabName}`).classList.add('active');
    }
    
    static async loadBatchSerialData(productId) {
        try {
            const locationId = AppState.currentLocation?.location_id;
            const items = await APIClient.get(`/products/${productId}/batch-serials${locationId ? `?location_id=${locationId}` : ''}`);
            
            const container = document.getElementById('batch-serial-list');
            if (items.length === 0) {
                container.innerHTML = '<div class="empty-state">No batch/serial items found</div>';
                return;
            }
            
            container.innerHTML = `
                <div class="batch-serial-grid">
                    ${items.map(item => `
                        <div class="batch-serial-item ${item.status}">
                            <div class="item-info">
                                ${item.batch_number ? `<div><strong>Batch:</strong> ${item.batch_number}</div>` : ''}
                                ${item.serial_number ? `<div><strong>Serial:</strong> ${item.serial_number}</div>` : ''}
                                ${item.expiry_date ? `<div><strong>Expires:</strong> ${new Date(item.expiry_date).toLocaleDateString()}</div>` : ''}
                                <div><strong>Status:</strong> <span class="status-badge ${item.status}">${item.status}</span></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            document.getElementById('batch-serial-list').innerHTML = 
                `<div class="error">Failed to load data: ${error.message}</div>`;
        }
    }
    
    static async addBatchSerial(productId) {
        if (!AppState.currentLocation) {
            NotificationManager.show('Please select a location first', 'warning');
            return;
        }
        
        const batchNumber = document.getElementById('batch-number')?.value;
        const serialNumber = document.getElementById('serial-number')?.value;
        const expiryDate = document.getElementById('expiry-date')?.value;
        
        const data = {
            product_id: productId,
            location_id: AppState.currentLocation.location_id,
            batch_number: batchNumber || null,
            serial_number: serialNumber || null,
            expiry_date: expiryDate || null
        };
        
        try {
            await APIClient.post('/batch-serials/', data);
            NotificationManager.show('Batch/Serial item added successfully!', 'success');
            document.getElementById('batch-serial-form').reset();
            await this.loadBatchSerialData(productId);
        } catch (error) {
            NotificationManager.show(`Failed to add item: ${error.message}`, 'error');
        }
    }
}

class ReorderManager {
    static async loadReorderAlerts() {
        try {
            AppState.reorderAlerts = await APIClient.get('/reorder-alerts/?status=pending');
            this.renderReorderAlerts();
            this.updateReorderBadge();
        } catch (error) {
            NotificationManager.show(`Failed to load reorder alerts: ${error.message}`, 'error');
        }
    }
    
    static renderReorderAlerts() {
        const container = document.getElementById('reorder-alerts');
        if (!container) return;
        
        if (AppState.reorderAlerts.length === 0) {
            container.innerHTML = '<div class="success">✅ No pending reorder alerts</div>';
            return;
        }
        
        container.innerHTML = `
            <div class="reorder-alerts-list">
                ${AppState.reorderAlerts.map(alert => `
                    <div class="reorder-alert-item">
                        <div class="alert-info">
                            <h4>Product ID: ${alert.product_id}</h4>
                            <p><strong>Current Stock:</strong> ${alert.current_stock}</p>
                            <p><strong>Reorder Level:</strong> ${alert.reorder_level}</p>
                            <p><strong>Suggested Quantity:</strong> ${alert.suggested_quantity}</p>
                            <p><strong>Created:</strong> ${new Date(alert.created_at).toLocaleDateString()}</p>
                        </div>
                        <div class="alert-actions">
                            <button onclick="ReorderManager.acknowledgeAlert(${alert.alert_id})" class="btn-primary">
                                Acknowledge
                            </button>
                            <button onclick="ReorderManager.createPurchaseOrder(${alert.alert_id})" class="btn-success">
                                Create PO
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    static updateReorderBadge() {
        const badge = document.getElementById('reorder-badge');
        if (badge) {
            badge.textContent = AppState.reorderAlerts.length;
            badge.style.display = AppState.reorderAlerts.length > 0 ? 'block' : 'none';
        }
    }
    
    static async acknowledgeAlert(alertId) {
        try {
            await APIClient.put(`/reorder-alerts/${alertId}/acknowledge`);
            NotificationManager.show('Alert acknowledged', 'success');
            await this.loadReorderAlerts();
        } catch (error) {
            NotificationManager.show(`Failed to acknowledge alert: ${error.message}`, 'error');
        }
    }
    
    static createPurchaseOrder(alertId) {
        // This would open a purchase order creation modal
        NotificationManager.show('Purchase order creation feature coming soon!', 'info');
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    // Load saved state
    const savedUser = localStorage.getItem('currentUser');
    const savedLocation = localStorage.getItem('currentLocation');
    
    if (savedUser) {
        AppState.currentUser = JSON.parse(savedUser);
    }
    
    if (savedLocation) {
        AppState.currentLocation = JSON.parse(savedLocation);
    }
    
    // Check authentication
    if (!AuthManager.isAuthenticated()) {
        showLoginForm();
        return;
    }
    
    // Initialize the app
    try {
        await LocationManager.loadLocations();
        await InventoryManager.loadInventory();
        await ReorderManager.loadReorderAlerts();
        
        // Set up periodic refresh
        setInterval(async () => {
            if (AppState.isOnline) {
                await ReorderManager.loadReorderAlerts();
            }
        }, 60000); // Check every minute
        
        NotificationManager.show('Application loaded successfully!', 'success');
        
    } catch (error) {
        NotificationManager.show(`Failed to initialize application: ${error.message}`, 'error');
    }
});

function showLoginForm() {
    document.body.innerHTML = `
        <div class="login-container">
            <div class="login-form">
                <h2>Electronics Store Login</h2>
                <form id="login-form">
                    <div class="form-group">
                        <label>Username:</label>
                        <input type="text" id="username" required>
                    </div>
                    <div class="form-group">
                        <label>Password:</label>
                        <input type="password" id="password" required>
                    </div>
                    <button type="submit" class="btn-primary">Login</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            await AuthManager.login(username, password);
            window.location.reload();
        } catch (error) {
            NotificationManager.show(error.message, 'error');
        }
    });
}

// Online/Offline handling
window.addEventListener('online', () => {
    AppState.isOnline = true;
    NotificationManager.show('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    AppState.isOnline = false;
    NotificationManager.show('Working offline', 'warning');
});

// Export for global access
window.AppState = AppState;
window.NotificationManager = NotificationManager;
window.APIClient = APIClient;
window.AuthManager = AuthManager;
window.LocationManager = LocationManager;
window.InventoryManager = InventoryManager;
window.BatchSerialManager = BatchSerialManager;
window.ReorderManager = ReorderManager;
