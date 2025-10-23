// preload.js - Secure bridge between main and renderer processes
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Product operations
  getProducts: () => ipcRenderer.invoke('db-get-products'),
  addProduct: (product) => ipcRenderer.invoke('db-add-product', product),
  updateProduct: (id, product) => ipcRenderer.invoke('db-update-product', id, product),
  deleteProduct: (id) => ipcRenderer.invoke('db-delete-product', id),
  getProduct: (id) => ipcRenderer.invoke('db-get-product', id),

  // Sale operations
  addSale: (sale) => ipcRenderer.invoke('db-add-sale', sale),
  getSales: () => ipcRenderer.invoke('db-get-sales'),

  // Analytics
  getAnalytics: () => ipcRenderer.invoke('db-get-analytics'),

  // Settings
  getSetting: (key) => ipcRenderer.invoke('db-get-setting', key),
  setSetting: (key, value) => ipcRenderer.invoke('db-set-setting', key, value),

  // Customer operations
  getCustomers: () => ipcRenderer.invoke('db-get-customers'),
  addCustomer: (customer) => ipcRenderer.invoke('db-add-customer', customer),
  updateCustomer: (id, customer) => ipcRenderer.invoke('db-update-customer', id, customer),
  deleteCustomer: (id) => ipcRenderer.invoke('db-delete-customer', id),
  getCustomer: (id) => ipcRenderer.invoke('db-get-customer', id),

  // Barcode operations
  getProductByBarcode: (barcode) => ipcRenderer.invoke('db-get-product-by-barcode', barcode),

  // Receipt operations
  getSaleByReceipt: (receiptNumber) => ipcRenderer.invoke('db-get-sale-by-receipt', receiptNumber),
  printReceipt: (receiptData) => ipcRenderer.invoke('print-receipt', receiptData),

  // Supplier operations
  getSuppliers: () => ipcRenderer.invoke('db-get-suppliers'),
  addSupplier: (supplier) => ipcRenderer.invoke('db-add-supplier', supplier),
  updateSupplier: (id, supplier) => ipcRenderer.invoke('db-update-supplier', id, supplier),
  deleteSupplier: (id) => ipcRenderer.invoke('db-delete-supplier', id),

  // Product variants
  getProductVariants: (productId) => ipcRenderer.invoke('db-get-product-variants', productId),
  addProductVariant: (variant) => ipcRenderer.invoke('db-add-product-variant', variant),

  // Export/Import operations
  exportProductsCSV: () => ipcRenderer.invoke('export-products-csv'),
  exportSalesCSV: (startDate, endDate) => ipcRenderer.invoke('export-sales-csv', startDate, endDate),
  importProductsCSV: () => ipcRenderer.invoke('import-products-csv'),
  exportReportPDF: (reportData, reportType) => ipcRenderer.invoke('export-report-pdf', reportData, reportType),

  // Advanced analytics
  getProfitAnalysis: (startDate, endDate) => ipcRenderer.invoke('db-get-profit-analysis', startDate, endDate),
  getCategoryProfitAnalysis: (startDate, endDate) => ipcRenderer.invoke('db-get-category-profit-analysis', startDate, endDate),
  getInventoryTurnover: () => ipcRenderer.invoke('db-get-inventory-turnover'),
  getReorderAnalysis: () => ipcRenderer.invoke('db-get-reorder-analysis'),

  // Menu event listeners
  onMenuNewProduct: (callback) => ipcRenderer.on('menu-new-product', callback),
  onMenuSwitchTab: (callback) => ipcRenderer.on('menu-switch-tab', callback),

  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});

// Expose a simple API for notifications
contextBridge.exposeInMainWorld('notificationAPI', {
  show: (title, body, options = {}) => {
    if (Notification.permission === 'granted') {
      return new Notification(title, { body, ...options });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          return new Notification(title, { body, ...options });
        }
      });
    }
  },
  requestPermission: () => Notification.requestPermission()
});
