// renderer.js - Frontend JavaScript for the Electron application

// Enhanced renderer.js with better error handling and user feedback

// Utility functions for user feedback
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type} fade-in`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        max-width: 300px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    `;
    
    if (type === 'success') {
        notification.style.background = '#28a745';
    } else if (type === 'error') {
        notification.style.background = '#dc3545';
    } else if (type === 'warning') {
        notification.style.background = '#ffc107';
        notification.style.color = '#212529';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

function validateForm(formData, requiredFields) {
    const errors = [];
    
    requiredFields.forEach(field => {
        const value = formData.get(field.name);
        if (!value || value.trim() === '') {
            errors.push(`${field.label} is required`);
        } else if (field.type === 'number' && (isNaN(value) || parseFloat(value) < 0)) {
            errors.push(`${field.label} must be a valid positive number`);
        } else if (field.type === 'price' && (isNaN(value) || parseFloat(value) <= 0)) {
            errors.push(`${field.label} must be greater than 0`);
        }
    });
    
    return errors;
}

function setLoading(element, isLoading, loadingText = 'Loading...') {
    if (isLoading) {
        element.innerHTML = `<div class="loading">${loadingText}</div>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const inventoryDisplay = document.getElementById('inventory-display');
    const addProductForm = document.getElementById('add-product-form');
    const editProductForm = document.getElementById('edit-product-form');
    const createSaleForm = document.getElementById('create-sale-form');
    const addCustomerForm = document.getElementById('add-customer-form');
    const addSupplierForm = document.getElementById('add-supplier-form');
    const addSaleItemBtn = document.getElementById('add-sale-item');
    const cancelEditBtn = document.getElementById('cancel-edit');
    // Tab elements
    const dashboardTab = document.getElementById('dashboard-tab');
    const inventoryTab = document.getElementById('inventory-tab');
    const customersTab = document.getElementById('customers-tab');
    const suppliersTab = document.getElementById('suppliers-tab');
    const posTab = document.getElementById('pos-tab');
    const reportsTab = document.getElementById('reports-tab');
    const advancedTab = document.getElementById('advanced-tab');
    
    // Section elements
    const dashboardSection = document.getElementById('dashboard-section');
    const inventorySection = document.getElementById('inventory-section');
    const customersSection = document.getElementById('customers-section');
    const suppliersSection = document.getElementById('suppliers-section');
    const posSection = document.getElementById('pos-section');
    const reportsSection = document.getElementById('reports-section');
    const advancedSection = document.getElementById('advanced-section');

    // Dashboard elements
    const totalProductsEl = document.getElementById('total-products');
    const lowStockCountEl = document.getElementById('low-stock-count');
    const totalSalesEl = document.getElementById('total-sales');
    const totalRevenueEl = document.getElementById('total-revenue');
    const lowStockDisplay = document.getElementById('low-stock-display');
    const recentSalesDisplay = document.getElementById('recent-sales-display');

    const API_BASE = 'http://localhost:8000';
    let isOnline = navigator.onLine;
    let topProductsChart = null;
    let salesTrendChart = null;

    // Check online status
    window.addEventListener('online', () => {
        isOnline = true;
        showNotification('Connection restored - syncing data', 'success');
        syncWithServer();
    });

    window.addEventListener('offline', () => {
        isOnline = false;
        showNotification('Working offline - data will sync when connection is restored', 'warning');
    });

    // Function to fetch inventory data (hybrid online/offline)
    async function fetchInventory() {
        setLoading(inventoryDisplay, true, 'Loading inventory data...');
        
        try {
            // Always try local database first
            const localData = await window.electronAPI.getProducts();
            displayInventory(localData);
            
            // If online, try to sync with server
            if (isOnline) {
                try {
                    const response = await fetch(`${API_BASE}/products`);
                    if (response.ok) {
                        const serverData = await response.json();
                        // Here you could implement sync logic to merge server and local data
                        showNotification('Inventory loaded from local database', 'success');
                    }
                } catch (serverError) {
                    console.log('Server unavailable, using local data:', serverError);
                    showNotification('Using local data - server unavailable', 'warning');
                }
            } else {
                showNotification('Inventory loaded from local database (offline)', 'success');
            }
        } catch (error) {
            console.error('Error fetching inventory:', error);
            inventoryDisplay.innerHTML = `<div class="error">
                <strong>Error Loading Inventory</strong><br>
                Failed to load inventory data from local database.<br>
                <button onclick="fetchInventory()" class="btn-primary" style="margin-top: 10px;">Retry</button>
            </div>`;
            showNotification('Failed to load inventory data', 'error');
        }
    }

    // Function to display inventory data
    function displayInventory(inventory) {
        if (!inventoryDisplay) {
            console.error("Inventory display element not found!");
            showNotification('Display error occurred', 'error');
            return;
        }

        const tbody = document.getElementById('products-tbody');
        if (tbody) {
            tbody.innerHTML = '';
            
            if (inventory.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-data">No products found. Add some products to get started!</td></tr>';
                return;
            }
            
            inventory.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.sku || 'N/A'}</td>
                    <td>${product.name}</td>
                    <td>${product.category || 'Uncategorized'}</td>
                    <td>$${parseFloat(product.price).toFixed(2)}</td>
                    <td class="${product.stock_quantity <= (product.min_stock_level || 10) ? 'low-stock' : ''}">${product.stock_quantity}</td>
                    <td>
                        <button onclick="editProduct(${product.id})" class="btn-small">Edit</button>
                        <button onclick="deleteProduct(${product.id})" class="btn-small btn-danger">Delete</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    }

    // Function to edit product
    window.editProduct = async function(productId) {
        try {
            const product = await window.electronAPI.getProduct(productId);
            document.getElementById('edit-product-id').value = product.id;
            document.getElementById('edit-product-name').value = product.name;
            document.getElementById('edit-product-price').value = product.price;
            document.getElementById('edit-product-stock').value = product.stock_quantity;
            document.getElementById('edit-product-section').style.display = 'block';
            document.getElementById('edit-product-section').scrollIntoView({ behavior: 'smooth' });
            showNotification('Product loaded for editing', 'success');
        } catch (error) {
            console.error('Error fetching product:', error);
            showNotification('Failed to load product for editing', 'error');
        }
    };

    // Function to delete product
    window.deleteProduct = async function(productId, productName) {
        if (!confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            await window.electronAPI.deleteProduct(productId);
            showNotification(`Product "${productName}" deleted successfully`, 'success');
            fetchInventory();
            
            // If online, also try to delete from server
            if (isOnline) {
                try {
                    await fetch(`${API_BASE}/products/${productId}`, { method: 'DELETE' });
                } catch (serverError) {
                    console.log('Failed to sync deletion with server:', serverError);
                }
            }
        } catch (error) {
            console.error('Error deleting product:', error);
            showNotification('Failed to delete product', 'error');
        }
    };

    // Handle add product form
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(addProductForm);
        
        // Validate form data
        const validationErrors = validateForm(formData, [
            { name: 'product-name', label: 'Product Name', type: 'text' },
            { name: 'product-price', label: 'Price', type: 'price' },
            { name: 'product-stock', label: 'Stock Quantity', type: 'number' }
        ]);
        
        if (validationErrors.length > 0) {
            showNotification(`Validation Error: ${validationErrors.join(', ')}`, 'error');
            return;
        }
        
        const productData = {
            name: formData.get('product-name').trim(),
            description: formData.get('product-description')?.trim() || '',
            price: parseFloat(formData.get('product-price')),
            stock_quantity: parseInt(formData.get('product-stock')),
            sku: formData.get('product-sku')?.trim() || ''
        };

        // Disable submit button during request
        const submitBtn = addProductForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding...';

        try {
            // Add to local database first
            await window.electronAPI.addProduct(productData);
            showNotification('Product added successfully!', 'success');
            addProductForm.reset();
            fetchInventory();
            
            // If online, also try to add to server
            if (isOnline) {
                try {
                    const response = await fetch(`${API_BASE}/products/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(productData)
                    });
                    if (!response.ok) {
                        console.log('Failed to sync with server, but saved locally');
                    }
                } catch (serverError) {
                    console.log('Server sync failed, but product saved locally:', serverError);
                }
            }
        } catch (error) {
            console.error('Error adding product:', error);
            showNotification(`Failed to add product: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // Handle edit product form
    editProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const productId = document.getElementById('edit-product-id').value;
        const formData = new FormData(editProductForm);
        
        // Validate form data
        const validationErrors = validateForm(formData, [
            { name: 'edit-product-name', label: 'Product Name', type: 'text' },
            { name: 'edit-product-price', label: 'Price', type: 'price' },
            { name: 'edit-product-stock', label: 'Stock Quantity', type: 'number' }
        ]);
        
        if (validationErrors.length > 0) {
            showNotification(`Validation Error: ${validationErrors.join(', ')}`, 'error');
            return;
        }
        
        const productData = {
            name: formData.get('edit-product-name').trim(),
            price: parseFloat(formData.get('edit-product-price')),
            stock_quantity: parseInt(formData.get('edit-product-stock'))
        };

        // Disable submit button during request
        const submitBtn = editProductForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Updating...';

        try {
            // Update in local database first
            await window.electronAPI.updateProduct(productId, productData);
            showNotification('Product updated successfully!', 'success');
            document.getElementById('edit-product-section').style.display = 'none';
            fetchInventory();
            
            // If online, also try to update on server
            if (isOnline) {
                try {
                    const response = await fetch(`${API_BASE}/products/${productId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(productData)
                    });
                    if (!response.ok) {
                        console.log('Failed to sync update with server, but saved locally');
                    }
                } catch (serverError) {
                    console.log('Server sync failed, but product updated locally:', serverError);
                }
            }
        } catch (error) {
            console.error('Error updating product:', error);
            showNotification(`Failed to update product: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // Cancel edit
    cancelEditBtn.addEventListener('click', () => {
        document.getElementById('edit-product-section').style.display = 'none';
    });

    // Handle add customer form
    if (addCustomerForm) {
        addCustomerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(addCustomerForm);
            
            const customerData = {
                name: formData.get('customer-name').trim(),
                email: formData.get('customer-email')?.trim() || '',
                phone: formData.get('customer-phone')?.trim() || '',
                address: formData.get('customer-address')?.trim() || '',
                city: formData.get('customer-city')?.trim() || ''
            };

            // Disable submit button during request
            const submitBtn = addCustomerForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Adding...';

            try {
                await window.electronAPI.addCustomer(customerData);
                showNotification('Customer added successfully!', 'success');
                addCustomerForm.reset();
                loadCustomers();
            } catch (error) {
                console.error('Error adding customer:', error);
                showNotification(`Failed to add customer: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }

    // Handle add supplier form
    if (addSupplierForm) {
        addSupplierForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(addSupplierForm);
            
            const supplierData = {
                name: formData.get('supplier-name').trim(),
                contact_person: formData.get('supplier-contact-person')?.trim() || '',
                email: formData.get('supplier-email')?.trim() || '',
                phone: formData.get('supplier-phone')?.trim() || '',
                address: formData.get('supplier-address')?.trim() || '',
                city: formData.get('supplier-city')?.trim() || '',
                country: formData.get('supplier-country')?.trim() || '',
                payment_terms: formData.get('supplier-payment-terms')?.trim() || '',
                notes: formData.get('supplier-notes')?.trim() || ''
            };

            // Disable submit button during request
            const submitBtn = addSupplierForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Adding...';

            try {
                await window.electronAPI.addSupplier(supplierData);
                showNotification('Supplier added successfully!', 'success');
                addSupplierForm.reset();
                loadSuppliers();
            } catch (error) {
                console.error('Error adding supplier:', error);
                showNotification(`Failed to add supplier: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }

    // Handle create sale form
    createSaleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const customerId = document.getElementById('sale-customer-id').value || null;
        const items = [];
        const saleItems = document.querySelectorAll('.sale-item');
        saleItems.forEach(item => {
            const productId = parseInt(item.querySelector('.sale-product-id').value);
            const quantity = parseInt(item.querySelector('.sale-quantity').value);
            const price = item.querySelector('.sale-price').value ? parseFloat(item.querySelector('.sale-price').value) : null;
            if (productId && quantity) {
                items.push({ product_id: productId, quantity, price });
            }
        });

        const saleData = { customer_id: customerId, items };

        try {
            const response = await fetch(`${API_BASE}/sales/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saleData)
            });
            if (response.ok) {
                alert('Sale created successfully!');
                createSaleForm.reset();
                fetchInventory();
            } else {
                const error = await response.json();
                alert(`Error creating sale: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    });

    // Add sale item
    addSaleItemBtn.addEventListener('click', () => {
        const saleItemsDiv = document.getElementById('sale-items');
        const newItem = document.createElement('div');
        newItem.className = 'sale-item';
        newItem.innerHTML = `
            <label>Product ID:</label>
            <input type="number" class="sale-product-id" required>
            <label>Quantity:</label>
            <input type="number" class="sale-quantity" required>
            <label>Price (optional):</label>
            <input type="number" class="sale-price" step="0.01">
            <button type="button" class="remove-item btn-danger">Remove</button>
        `;
        saleItemsDiv.appendChild(newItem);
        newItem.querySelector('.remove-item').addEventListener('click', () => {
            saleItemsDiv.removeChild(newItem);
        });
    });

    // Remove item handler for initial item
    document.querySelector('.remove-item').addEventListener('click', (e) => {
        e.target.parentElement.remove();
    });

    // Tab switching functionality
    const tabs = [
        { tab: dashboardTab, section: dashboardSection, name: 'dashboard' },
        { tab: inventoryTab, section: inventorySection, name: 'inventory' },
        { tab: customersTab, section: customersSection, name: 'customers' },
        { tab: suppliersTab, section: suppliersSection, name: 'suppliers' },
        { tab: posTab, section: posSection, name: 'pos' },
        { tab: reportsTab, section: reportsSection, name: 'reports' },
        { tab: advancedTab, section: advancedSection, name: 'advanced' }
    ];

    function switchToTab(activeTabName) {
        tabs.forEach(({ tab, section, name }) => {
            if (name === activeTabName) {
                tab.classList.add('active');
                section.style.display = 'block';
                
                // Load specific data when switching to certain tabs
                if (name === 'dashboard') {
                    loadDashboardData();
                } else if (name === 'inventory') {
                    loadProducts();
                } else if (name === 'customers') {
                    loadCustomers();
                } else if (name === 'suppliers') {
                    loadSuppliers();
                } else if (name === 'reports') {
                    loadDashboard();
                }
            } else {
                tab.classList.remove('active');
                section.style.display = 'none';
            }
        });
    }

    // Add event listeners for all tabs
    tabs.forEach(({ tab, name }) => {
        if (tab) {
            tab.addEventListener('click', () => switchToTab(name));
        }
    });

    // Profit Analysis Tab Switching
    const analysisTabButtons = [
        { id: 'product-profit-tab', content: 'product-profit-analysis' },
        { id: 'category-profit-tab', content: 'category-profit-analysis' },
        { id: 'inventory-turnover-tab', content: 'inventory-turnover-analysis' },
        { id: 'reorder-analysis-tab', content: 'reorder-analysis-content' }
    ];

    function switchAnalysisTab(activeTabId) {
        analysisTabButtons.forEach(({ id, content }) => {
            const tabButton = document.getElementById(id);
            const tabContent = document.getElementById(content);
            
            if (tabButton && tabContent) {
                if (id === activeTabId) {
                    tabButton.classList.add('active');
                    tabContent.style.display = 'block';
                } else {
                    tabButton.classList.remove('active');
                    tabContent.style.display = 'none';
                }
            }
        });
    }

    // Add click handlers for analysis tabs
    analysisTabButtons.forEach(({ id }) => {
        const tabButton = document.getElementById(id);
        if (tabButton) {
            tabButton.addEventListener('click', () => switchAnalysisTab(id));
        }
    });

    // Generate Analysis Button Handler
    const generateAnalysisBtn = document.getElementById('generate-profit-analysis-btn');
    if (generateAnalysisBtn) {
        generateAnalysisBtn.addEventListener('click', async () => {
            const startDate = document.getElementById('analysis-start-date').value;
            const endDate = document.getElementById('analysis-end-date').value;
            
            if (!startDate || !endDate) {
                showNotification('Please select both start and end dates for analysis', 'warning');
                return;
            }

            generateAnalysisBtn.disabled = true;
            generateAnalysisBtn.textContent = 'Generating...';

            try {
                await generateAllAnalysis(startDate, endDate);
                showNotification('Analysis generated successfully!', 'success');
            } catch (error) {
                console.error('Error generating analysis:', error);
                showNotification('Failed to generate analysis', 'error');
            } finally {
                generateAnalysisBtn.disabled = false;
                generateAnalysisBtn.textContent = 'Generate Analysis';
            }
        });
    }

    // Load dashboard data for the dashboard tab
    async function loadDashboardData() {
        try {
            const products = await window.electronAPI.getProducts();
            const customers = await window.electronAPI.getCustomers();
            const suppliers = await window.electronAPI.getSuppliers();
            
            // Update dashboard stats
            const dashTotalProducts = document.getElementById('dash-total-products');
            const dashLowStock = document.getElementById('dash-low-stock');
            const dashTotalCustomers = document.getElementById('dash-total-customers');
            const dashTotalSuppliers = document.getElementById('dash-total-suppliers');
            
            if (dashTotalProducts) dashTotalProducts.textContent = products.length;
            if (dashLowStock) {
                const lowStockCount = products.filter(p => p.stock_quantity <= (p.min_stock_level || 10)).length;
                dashLowStock.textContent = lowStockCount;
            }
            if (dashTotalCustomers) dashTotalCustomers.textContent = customers.length;
            if (dashTotalSuppliers) dashTotalSuppliers.textContent = suppliers.length;
            
            showNotification('Dashboard data loaded', 'success');
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            showNotification('Failed to load dashboard data', 'error');
        }
    }

    // Load comprehensive dashboard for reports
    async function loadDashboard() {
        try {
            // Load analytics data
            const analytics = await window.electronAPI.getAnalytics();
            const products = await window.electronAPI.getProducts();
            const sales = await window.electronAPI.getSales();
            
            // Update metrics cards
            updateMetricsCards(products, analytics, sales);
            
            // Update charts
            updateCharts(analytics);
            
            // Update low stock display
            displayLowStockItems(analytics.lowStockProducts);
            
            // Update recent sales
            displayRecentSales(sales.slice(0, 10));
            
            showNotification('Dashboard loaded successfully', 'success');
        } catch (error) {
            console.error('Error loading dashboard:', error);
            showNotification('Failed to load dashboard data', 'error');
        }
    }
    
    // Update metrics cards
    function updateMetricsCards(products, analytics, sales) {
        totalProductsEl.textContent = products.length;
        lowStockCountEl.textContent = analytics.lowStockProducts.length;
        
        // Calculate 30-day totals
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        const recentSales = sales.filter(sale => new Date(sale.created_at) >= thirtyDaysAgo);
        
        totalSalesEl.textContent = recentSales.length;
        
        const totalRevenue = recentSales.reduce((sum, sale) => sum + parseFloat(sale.total_amount || 0), 0);
        totalRevenueEl.textContent = `$${totalRevenue.toFixed(2)}`;
    }
    
    // Update charts
    function updateCharts(analytics) {
        // Destroy existing charts
        if (topProductsChart) {
            topProductsChart.destroy();
        }
        if (salesTrendChart) {
            salesTrendChart.destroy();
        }
        
        // Top Products Chart
        const topProductsCtx = document.getElementById('top-products-chart').getContext('2d');
        topProductsChart = new Chart(topProductsCtx, {
            type: 'doughnut',
            data: {
                labels: analytics.topProducts.map(p => p.name),
                datasets: [{
                    data: analytics.topProducts.map(p => p.total_sold),
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f093fb',
                        '#f5576c',
                        '#4facfe'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const product = analytics.topProducts[context.dataIndex];
                                return `${product.name}: ${product.total_sold} sold ($${parseFloat(product.total_revenue).toFixed(2)})`;
                            }
                        }
                    }
                }
            }
        });
        
        // Sales Trend Chart
        const salesTrendCtx = document.getElementById('sales-trend-chart').getContext('2d');
        salesTrendChart = new Chart(salesTrendCtx, {
            type: 'line',
            data: {
                labels: analytics.salesReport.map(r => new Date(r.sale_date).toLocaleDateString()),
                datasets: [{
                    label: 'Daily Revenue',
                    data: analytics.salesReport.map(r => parseFloat(r.total_revenue)),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7
                        }
                    }
                }
            }
        });
    }
    
    // Display low stock items
    function displayLowStockItems(lowStockProducts) {
        if (lowStockProducts.length === 0) {
            lowStockDisplay.innerHTML = '<div class="success">✅ All products are well stocked!</div>';
            return;
        }
        
        const itemsHtml = lowStockProducts.map(product => {
            const isCritical = product.stock_quantity <= 5;
            return `
                <div class="low-stock-item ${isCritical ? 'critical' : ''}">
                    <div class="low-stock-info">
                        <div class="low-stock-name">${product.name}</div>
                        <div class="low-stock-details">
                            SKU: ${product.sku || 'N/A'} | Price: $${parseFloat(product.price).toFixed(2)}
                        </div>
                    </div>
                    <div class="stock-level ${isCritical ? 'critical' : 'low'}">
                        ${product.stock_quantity} left
                    </div>
                </div>
            `;
        }).join('');
        
        lowStockDisplay.innerHTML = itemsHtml;
    }
    
    // Display recent sales
    function displayRecentSales(recentSales) {
        if (recentSales.length === 0) {
            recentSalesDisplay.innerHTML = '<div class="loading">No sales recorded yet.</div>';
            return;
        }
        
        const tableHtml = `
            <table class="sales-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Items</th>
                        <th>Products</th>
                        <th>Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${recentSales.map(sale => `
                        <tr>
                            <td class="sale-date">${new Date(sale.created_at).toLocaleDateString()}</td>
                            <td>${sale.item_count}</td>
                            <td>${sale.product_names || 'N/A'}</td>
                            <td class="sale-amount">$${parseFloat(sale.total_amount).toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        recentSalesDisplay.innerHTML = tableHtml;
    }

    // Sync with server function
    async function syncWithServer() {
        if (!isOnline) return;
        
        try {
            // This would implement bidirectional sync logic
            // For now, just log that sync is happening
            console.log('Syncing with server...');
            // You could implement:
            // 1. Push local changes to server
            // 2. Pull server changes to local
            // 3. Resolve conflicts
        } catch (error) {
            console.error('Sync failed:', error);
        }
    }

    // Menu event handlers
    if (window.electronAPI) {
        window.electronAPI.onMenuNewProduct(() => {
            document.getElementById('product-name').focus();
            showNotification('Ready to add new product', 'success');
        });
        
        window.electronAPI.onMenuSwitchTab((event, tab) => {
            if (tab === 'inventory') {
                inventoryTab.click();
            } else if (tab === 'reports') {
                reportsTab.click();
            }
        });
    }
    
    // Initialize notification permissions
    if (window.notificationAPI) {
        window.notificationAPI.requestPermission();
    }
    
    // Load customers and display them
    async function loadCustomers() {
        try {
            const customers = await window.electronAPI.getCustomers();
            const tbody = document.getElementById('customers-tbody');
            
            if (tbody) {
                tbody.innerHTML = '';
                
                if (customers.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="no-data">No customers found</td></tr>';
                } else {
                    customers.forEach(customer => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${customer.name}</td>
                            <td>${customer.email || '-'}</td>
                            <td>${customer.phone || '-'}</td>
                            <td>${customer.city || '-'}</td>
                            <td>${customer.loyalty_points || 0}</td>
                            <td>
                                <button onclick="editCustomer(${customer.id})" class="btn-small">Edit</button>
                                <button onclick="deleteCustomer(${customer.id})" class="btn-small btn-danger">Delete</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading customers:', error);
            showNotification('Failed to load customers', 'error');
        }
    }

    // Load suppliers and display them
    async function loadSuppliers() {
        try {
            const suppliers = await window.electronAPI.getSuppliers();
            const tbody = document.getElementById('suppliers-tbody');
            
            if (tbody) {
                tbody.innerHTML = '';
                
                if (suppliers.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="no-data">No suppliers found</td></tr>';
                } else {
                    suppliers.forEach(supplier => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${supplier.name}</td>
                            <td>${supplier.contact_person || '-'}</td>
                            <td>${supplier.email || '-'}</td>
                            <td>${supplier.phone || '-'}</td>
                            <td>${supplier.city || '-'}</td>
                            <td>
                                <button onclick="editSupplier(${supplier.id})" class="btn-small">Edit</button>
                                <button onclick="deleteSupplier(${supplier.id})" class="btn-small btn-danger">Delete</button>
                            </td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading suppliers:', error);
            showNotification('Failed to load suppliers', 'error');
        }
    }

    // Load products and display them
    async function loadProducts() {
        try {
            const products = await window.electronAPI.getProducts();
            const tbody = document.getElementById('products-tbody');
            if (tbody) {
                tbody.innerHTML = '';

                if (products.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="no-data">No products found. Add some products to get started!</td></tr>';
                    return;
                }

                products.forEach(product => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${product.sku || 'N/A'}</td>
                        <td>${product.name}</td>
                        <td>${product.category || 'Uncategorized'}</td>
                        <td>$${parseFloat(product.price).toFixed(2)}</td>
                        <td class="${product.stock_quantity <= (product.min_stock_level || 10) ? 'low-stock' : ''}">${product.stock_quantity}</td>
                        <td>
                            <button onclick="editProduct(${product.id})" class="btn-small">Edit</button>
                            <button onclick="deleteProduct(${product.id})" class="btn-small btn-danger">Delete</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error loading products:', error);
            showNotification('Failed to load products', 'error');
        }
    }

    // Generate All Analysis Function
    async function generateAllAnalysis(startDate, endDate) {
        try {
            // Generate all types of analysis
            await Promise.all([
                generateProductProfitAnalysis(startDate, endDate),
                generateCategoryProfitAnalysis(startDate, endDate),
                generateInventoryTurnoverAnalysis(startDate, endDate),
                generateReorderAnalysis()
            ]);
        } catch (error) {
            console.error('Error in generateAllAnalysis:', error);
            throw error;
        }
    }

    // Product Profit Analysis
    async function generateProductProfitAnalysis(startDate, endDate) {
        try {
            const profitData = await window.electronAPI.getProfitAnalysis(startDate, endDate);
            const tableContainer = document.getElementById('product-profit-table');
            
            if (!profitData || profitData.length === 0) {
                tableContainer.innerHTML = '<p class="no-data">No profit data available for the selected period</p>';
                return;
            }

            const tableHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Units Sold</th>
                            <th>Revenue</th>
                            <th>Cost</th>
                            <th>Profit</th>
                            <th>Margin %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${profitData.map(item => `
                            <tr>
                                <td>${item.name}</td>
                                <td>${item.units_sold || 0}</td>
                                <td>$${parseFloat(item.total_revenue || 0).toFixed(2)}</td>
                                <td>$${parseFloat(item.total_cost || 0).toFixed(2)}</td>
                                <td class="${parseFloat(item.profit || 0) >= 0 ? 'profit-positive' : 'profit-negative'}">
                                    $${parseFloat(item.profit || 0).toFixed(2)}
                                </td>
                                <td>${parseFloat(item.profit_margin || 0).toFixed(1)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            tableContainer.innerHTML = tableHTML;
        } catch (error) {
            console.error('Error generating product profit analysis:', error);
            document.getElementById('product-profit-table').innerHTML = '<p class="error">Failed to load product profit data</p>';
        }
    }

    // Category Profit Analysis
    async function generateCategoryProfitAnalysis(startDate, endDate) {
        try {
            const products = await window.electronAPI.getProducts();
            const sales = await window.electronAPI.getSales();
            
            // Filter sales by date range
            const filteredSales = sales.filter(sale => {
                const saleDate = new Date(sale.created_at);
                return saleDate >= new Date(startDate) && saleDate <= new Date(endDate);
            });

            // Group by category and calculate profits
            const categoryData = {};
            
            for (const sale of filteredSales) {
                if (sale.items) {
                    for (const item of sale.items) {
                        const product = products.find(p => p.id === item.product_id);
                        if (product) {
                            const category = product.category || 'Uncategorized';
                            if (!categoryData[category]) {
                                categoryData[category] = {
                                    revenue: 0,
                                    cost: 0,
                                    units: 0
                                };
                            }
                            
                            const revenue = parseFloat(item.total_price || 0);
                            const cost = parseFloat(product.cost || 0) * parseInt(item.quantity || 0);
                            
                            categoryData[category].revenue += revenue;
                            categoryData[category].cost += cost;
                            categoryData[category].units += parseInt(item.quantity || 0);
                        }
                    }
                }
            }

            const tableContainer = document.getElementById('category-profit-table');
            
            if (Object.keys(categoryData).length === 0) {
                tableContainer.innerHTML = '<p class="no-data">No category data available for the selected period</p>';
                return;
            }

            const tableHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Units Sold</th>
                            <th>Revenue</th>
                            <th>Cost</th>
                            <th>Profit</th>
                            <th>Margin %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(categoryData).map(([category, data]) => {
                            const profit = data.revenue - data.cost;
                            const margin = data.revenue > 0 ? (profit / data.revenue) * 100 : 0;
                            return `
                                <tr>
                                    <td>${category}</td>
                                    <td>${data.units}</td>
                                    <td>$${data.revenue.toFixed(2)}</td>
                                    <td>$${data.cost.toFixed(2)}</td>
                                    <td class="${profit >= 0 ? 'profit-positive' : 'profit-negative'}">
                                        $${profit.toFixed(2)}
                                    </td>
                                    <td>${margin.toFixed(1)}%</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
            
            tableContainer.innerHTML = tableHTML;
        } catch (error) {
            console.error('Error generating category profit analysis:', error);
            document.getElementById('category-profit-table').innerHTML = '<p class="error">Failed to load category profit data</p>';
        }
    }

    // Inventory Turnover Analysis
    async function generateInventoryTurnoverAnalysis(startDate, endDate) {
        try {
            const products = await window.electronAPI.getProducts();
            const sales = await window.electronAPI.getSales();
            
            // Calculate turnover for each product
            const turnoverData = products.map(product => {
                // Filter sales for this product in the date range
                const productSales = sales.filter(sale => {
                    const saleDate = new Date(sale.created_at);
                    return saleDate >= new Date(startDate) && 
                           saleDate <= new Date(endDate) &&
                           sale.items && 
                           sale.items.some(item => item.product_id === product.id);
                });

                // Calculate total units sold
                const totalSold = productSales.reduce((sum, sale) => {
                    const productItems = sale.items.filter(item => item.product_id === product.id);
                    return sum + productItems.reduce((itemSum, item) => itemSum + parseInt(item.quantity || 0), 0);
                }, 0);

                // Calculate turnover ratio
                const avgInventory = product.stock_quantity + (totalSold / 2); // Simplified average
                const turnoverRatio = avgInventory > 0 ? totalSold / avgInventory : 0;
                
                // Calculate days to sell current inventory
                const daysPeriod = Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24));
                const dailySalesRate = daysPeriod > 0 ? totalSold / daysPeriod : 0;
                const daysToSell = dailySalesRate > 0 ? product.stock_quantity / dailySalesRate : 999;

                return {
                    ...product,
                    totalSold,
                    turnoverRatio,
                    daysToSell: Math.round(daysToSell)
                };
            });

            const tableContainer = document.getElementById('inventory-turnover-table');
            
            const tableHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Current Stock</th>
                            <th>Units Sold</th>
                            <th>Turnover Ratio</th>
                            <th>Days to Sell</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${turnoverData.map(item => {
                            let status = 'Normal';
                            let statusClass = '';
                            
                            if (item.daysToSell > 90) {
                                status = 'Slow Moving';
                                statusClass = 'status-slow';
                            } else if (item.daysToSell < 30) {
                                status = 'Fast Moving';
                                statusClass = 'status-fast';
                            }
                            
                            return `
                                <tr>
                                    <td>${item.name}</td>
                                    <td>${item.stock_quantity}</td>
                                    <td>${item.totalSold}</td>
                                    <td>${item.turnoverRatio.toFixed(2)}</td>
                                    <td>${item.daysToSell > 999 ? '999+' : item.daysToSell}</td>
                                    <td class="${statusClass}">${status}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
            
            tableContainer.innerHTML = tableHTML;
        } catch (error) {
            console.error('Error generating inventory turnover analysis:', error);
            document.getElementById('inventory-turnover-table').innerHTML = '<p class="error">Failed to load inventory turnover data</p>';
        }
    }

    // Reorder Analysis
    async function generateReorderAnalysis() {
        try {
            const reorderData = await window.electronAPI.getReorderAnalysis();
            const tableContainer = document.getElementById('reorder-analysis-table');
            
            if (!reorderData || reorderData.length === 0) {
                tableContainer.innerHTML = '<p class="no-data">No reorder analysis data available</p>';
                return;
            }

            const tableHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Product Name</th>
                            <th>Current Stock</th>
                            <th>Min Level</th>
                            <th>Avg Daily Sales</th>
                            <th>Days Remaining</th>
                            <th>Reorder Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${reorderData.map(item => `
                            <tr>
                                <td>${item.name}</td>
                                <td class="${item.stock_quantity <= item.min_stock_level ? 'low-stock' : ''}">${item.stock_quantity}</td>
                                <td>${item.min_stock_level || 10}</td>
                                <td>${parseFloat(item.avg_daily_sales || 0).toFixed(2)}</td>
                                <td>${parseFloat(item.days_of_stock_remaining || 0).toFixed(0)}</td>
                                <td class="reorder-${item.reorder_status?.toLowerCase() || 'ok'}">
                                    ${item.reorder_status || 'OK'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            tableContainer.innerHTML = tableHTML;
        } catch (error) {
            console.error('Error generating reorder analysis:', error);
            document.getElementById('reorder-analysis-table').innerHTML = '<p class="error">Failed to load reorder analysis data</p>';
        }
    }

    // Call the fetch function when the page loads
    fetchInventory();
    
    // Load initial dashboard data
    loadDashboardData();
});

// Global functions for window access
window.fetchInventory = () => {
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
};

window.fetchReports = () => {
    // Trigger dashboard reload
    document.getElementById('reports-tab').click();
};
