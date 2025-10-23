const electron = require('electron');
const { app, BrowserWindow, ipcMain, Menu } = electron;
const path = require('path');
const DatabaseManager = require('./database');

let mainWindow;
let dbManager;

// Initialize database
async function initializeDatabase() {
  dbManager = new DatabaseManager();
  try {
    await dbManager.initialize();
    console.log('Database initialized successfully');
  } catch (error) {
    console.error('Failed to initialize database:', error);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'), // Add app icon if available
    show: false // Don't show until ready
  });

  mainWindow.loadFile('index.html');

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Product',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-new-product');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Inventory',
          accelerator: 'CmdOrCtrl+1',
          click: () => {
            mainWindow.webContents.send('menu-switch-tab', 'inventory');
          }
        },
        {
          label: 'Reports',
          accelerator: 'CmdOrCtrl+2',
          click: () => {
            mainWindow.webContents.send('menu-switch-tab', 'reports');
          }
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            // Show about dialog
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Electronics Store',
              message: 'Electronics Store Inventory Management',
              detail: 'Version 1.0.0\nA modern desktop application for managing electronics inventory.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(async () => {
  await initializeDatabase();
  createWindow();
  createMenu();
});

app.on('window-all-closed', () => {
  if (dbManager) {
    dbManager.close();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for database operations
ipcMain.handle('db-get-products', async () => {
  try {
    return await dbManager.getProducts();
  } catch (error) {
    console.error('Error getting products:', error);
    throw error;
  }
});

ipcMain.handle('db-add-product', async (event, product) => {
  try {
    return await dbManager.addProduct(product);
  } catch (error) {
    console.error('Error adding product:', error);
    throw error;
  }
});

ipcMain.handle('db-update-product', async (event, id, product) => {
  try {
    return await dbManager.updateProduct(id, product);
  } catch (error) {
    console.error('Error updating product:', error);
    throw error;
  }
});

ipcMain.handle('db-delete-product', async (event, id) => {
  try {
    return await dbManager.deleteProduct(id);
  } catch (error) {
    console.error('Error deleting product:', error);
    throw error;
  }
});

ipcMain.handle('db-get-product', async (event, id) => {
  try {
    return await dbManager.getProduct(id);
  } catch (error) {
    console.error('Error getting product:', error);
    throw error;
  }
});

ipcMain.handle('db-add-sale', async (event, sale) => {
  try {
    return await dbManager.addSale(sale);
  } catch (error) {
    console.error('Error adding sale:', error);
    throw error;
  }
});

ipcMain.handle('db-get-sales', async () => {
  try {
    return await dbManager.getSales();
  } catch (error) {
    console.error('Error getting sales:', error);
    throw error;
  }
});

ipcMain.handle('db-get-analytics', async () => {
  try {
    const topProducts = await dbManager.getTopSellingProducts(5);
    const lowStockProducts = await dbManager.getLowStockProducts(10);
    const today = new Date().toISOString().split('T')[0];
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const salesReport = await dbManager.getSalesReport(thirtyDaysAgo, today);
    
    return {
      topProducts,
      lowStockProducts,
      salesReport
    };
  } catch (error) {
    console.error('Error getting analytics:', error);
    throw error;
  }
});

ipcMain.handle('db-get-setting', async (event, key) => {
  try {
    return await dbManager.getSetting(key);
  } catch (error) {
    console.error('Error getting setting:', error);
    throw error;
  }
});

ipcMain.handle('db-set-setting', async (event, key, value) => {
  try {
    return await dbManager.setSetting(key, value);
  } catch (error) {
    console.error('Error setting setting:', error);
    throw error;
  }
});

// Customer management IPC handlers
ipcMain.handle('db-get-customers', async () => {
  try {
    return await dbManager.getCustomers();
  } catch (error) {
    console.error('Error getting customers:', error);
    throw error;
  }
});

ipcMain.handle('db-add-customer', async (event, customer) => {
  try {
    return await dbManager.addCustomer(customer);
  } catch (error) {
    console.error('Error adding customer:', error);
    throw error;
  }
});

ipcMain.handle('db-update-customer', async (event, id, customer) => {
  try {
    return await dbManager.updateCustomer(id, customer);
  } catch (error) {
    console.error('Error updating customer:', error);
    throw error;
  }
});

ipcMain.handle('db-delete-customer', async (event, id) => {
  try {
    return await dbManager.deleteCustomer(id);
  } catch (error) {
    console.error('Error deleting customer:', error);
    throw error;
  }
});

ipcMain.handle('db-get-customer', async (event, id) => {
  try {
    return await dbManager.getCustomer(id);
  } catch (error) {
    console.error('Error getting customer:', error);
    throw error;
  }
});

// Barcode operations
ipcMain.handle('db-get-product-by-barcode', async (event, barcode) => {
  try {
    return await dbManager.getProductByBarcode(barcode);
  } catch (error) {
    console.error('Error getting product by barcode:', error);
    throw error;
  }
});

// Receipt operations
ipcMain.handle('db-get-sale-by-receipt', async (event, receiptNumber) => {
  try {
    return await dbManager.getSaleByReceiptNumber(receiptNumber);
  } catch (error) {
    console.error('Error getting sale by receipt:', error);
    throw error;
  }
});

// Print receipt
ipcMain.handle('print-receipt', async (event, receiptData) => {
  try {
    const PosPrinter = require('electron-pos-printer');
    const options = {
      preview: false,
      width: '170px',
      margin: '0 0 0 0',
      copies: 1,
      printerName: '',
      timeOutPerLine: 400
    };

    const data = [
      {
        type: 'text',
        value: receiptData.storeName || 'Electronics Store',
        style: { fontWeight: "700", textAlign: 'center', fontSize: "18px" }
      },
      {
        type: 'text',
        value: receiptData.storeAddress || 'Store Address',
        style: { textAlign: 'center', fontSize: "12px" }
      },
      {
        type: 'text',
        value: `Receipt: ${receiptData.receiptNumber}`,
        style: { textAlign: 'center', fontSize: "12px", marginBottom: "10px" }
      },
      {
        type: 'text',
        value: `Date: ${new Date(receiptData.date).toLocaleString()}`,
        style: { fontSize: "12px" }
      }
    ];

    // Add customer info if available
    if (receiptData.customer) {
      data.push({
        type: 'text',
        value: `Customer: ${receiptData.customer.name}`,
        style: { fontSize: "12px" }
      });
    }

    data.push({
      type: 'text',
      value: '================================',
      style: { fontSize: "12px" }
    });

    // Add items
    receiptData.items.forEach(item => {
      data.push({
        type: 'text',
        value: `${item.product_name} x${item.quantity}`,
        style: { fontSize: "12px" }
      });
      data.push({
        type: 'text',
        value: `  $${item.unit_price.toFixed(2)} each = $${item.total_price.toFixed(2)}`,
        style: { fontSize: "10px", textAlign: 'right' }
      });
    });

    data.push({
      type: 'text',
      value: '================================',
      style: { fontSize: "12px" }
    });

    // Add totals
    data.push({
      type: 'text',
      value: `Subtotal: $${receiptData.subtotal.toFixed(2)}`,
      style: { fontSize: "12px", textAlign: 'right' }
    });

    if (receiptData.taxAmount > 0) {
      data.push({
        type: 'text',
        value: `Tax: $${receiptData.taxAmount.toFixed(2)}`,
        style: { fontSize: "12px", textAlign: 'right' }
      });
    }

    if (receiptData.discountAmount > 0) {
      data.push({
        type: 'text',
        value: `Discount: -$${receiptData.discountAmount.toFixed(2)}`,
        style: { fontSize: "12px", textAlign: 'right' }
      });
    }

    data.push({
      type: 'text',
      value: `TOTAL: $${receiptData.totalAmount.toFixed(2)}`,
      style: { fontSize: "14px", fontWeight: "700", textAlign: 'right' }
    });

    data.push({
      type: 'text',
      value: `Payment: ${receiptData.paymentMethod}`,
      style: { fontSize: "12px", textAlign: 'right' }
    });

    data.push({
      type: 'text',
      value: 'Thank you for your business!',
      style: { fontSize: "12px", textAlign: 'center', marginTop: "10px" }
    });

    await PosPrinter.print(data, options);
    return { success: true };
  } catch (error) {
    console.error('Error printing receipt:', error);
    throw error;
  }
});

// Supplier management IPC handlers
ipcMain.handle('db-get-suppliers', async () => {
  try {
    return await dbManager.getSuppliers();
  } catch (error) {
    console.error('Error getting suppliers:', error);
    throw error;
  }
});

ipcMain.handle('db-add-supplier', async (event, supplier) => {
  try {
    return await dbManager.addSupplier(supplier);
  } catch (error) {
    console.error('Error adding supplier:', error);
    throw error;
  }
});

ipcMain.handle('db-update-supplier', async (event, id, supplier) => {
  try {
    return await dbManager.updateSupplier(id, supplier);
  } catch (error) {
    console.error('Error updating supplier:', error);
    throw error;
  }
});

ipcMain.handle('db-delete-supplier', async (event, id) => {
  try {
    return await dbManager.deleteSupplier(id);
  } catch (error) {
    console.error('Error deleting supplier:', error);
    throw error;
  }
});

// Product variants IPC handlers
ipcMain.handle('db-get-product-variants', async (event, productId) => {
  try {
    return await dbManager.getProductVariants(productId);
  } catch (error) {
    console.error('Error getting product variants:', error);
    throw error;
  }
});

ipcMain.handle('db-add-product-variant', async (event, variant) => {
  try {
    return await dbManager.addProductVariant(variant);
  } catch (error) {
    console.error('Error adding product variant:', error);
    throw error;
  }
});

// Export/Import IPC handlers
ipcMain.handle('export-products-csv', async () => {
  try {
    const products = await dbManager.exportProductsToCSV();
    const createCsvWriter = require('csv-writer').createObjectCsvWriter;
    const path = require('path');
    const { dialog } = require('electron');
    
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Export Products to CSV',
      defaultPath: `products-export-${new Date().toISOString().split('T')[0]}.csv`,
      filters: [{ name: 'CSV Files', extensions: ['csv'] }]
    });
    
    if (!result.canceled) {
      const csvWriter = createCsvWriter({
        path: result.filePath,
        header: [
          { id: 'name', title: 'Name' },
          { id: 'description', title: 'Description' },
          { id: 'price', title: 'Price' },
          { id: 'cost', title: 'Cost' },
          { id: 'stock_quantity', title: 'Stock Quantity' },
          { id: 'min_stock_level', title: 'Min Stock Level' },
          { id: 'sku', title: 'SKU' },
          { id: 'barcode', title: 'Barcode' },
          { id: 'category', title: 'Category' },
          { id: 'supplier_name', title: 'Supplier' }
        ]
      });
      
      await csvWriter.writeRecords(products);
      return { success: true, filePath: result.filePath };
    }
    
    return { success: false, message: 'Export cancelled' };
  } catch (error) {
    console.error('Error exporting products:', error);
    throw error;
  }
});

ipcMain.handle('export-sales-csv', async (event, startDate, endDate) => {
  try {
    const sales = await dbManager.exportSalesToCSV(startDate, endDate);
    const createCsvWriter = require('csv-writer').createObjectCsvWriter;
    const { dialog } = require('electron');
    
    const result = await dialog.showSaveDialog(mainWindow, {
      title: 'Export Sales to CSV',
      defaultPath: `sales-export-${startDate}-to-${endDate}.csv`,
      filters: [{ name: 'CSV Files', extensions: ['csv'] }]
    });
    
    if (!result.canceled) {
      const csvWriter = createCsvWriter({
        path: result.filePath,
        header: [
          { id: 'receipt_number', title: 'Receipt Number' },
          { id: 'created_at', title: 'Date' },
          { id: 'customer_name', title: 'Customer' },
          { id: 'subtotal', title: 'Subtotal' },
          { id: 'tax_amount', title: 'Tax' },
          { id: 'discount_amount', title: 'Discount' },
          { id: 'total_amount', title: 'Total' },
          { id: 'payment_method', title: 'Payment Method' }
        ]
      });
      
      await csvWriter.writeRecords(sales);
      return { success: true, filePath: result.filePath };
    }
    
    return { success: false, message: 'Export cancelled' };
  } catch (error) {
    console.error('Error exporting sales:', error);
    throw error;
  }
});

ipcMain.handle('import-products-csv', async () => {
  try {
    const { dialog } = require('electron');
    const fs = require('fs');
    const csv = require('csv-parser');
    
    const result = await dialog.showOpenDialog(mainWindow, {
      title: 'Import Products from CSV',
      filters: [{ name: 'CSV Files', extensions: ['csv'] }],
      properties: ['openFile']
    });
    
    if (!result.canceled) {
      const products = [];
      
      return new Promise((resolve, reject) => {
        fs.createReadStream(result.filePaths[0])
          .pipe(csv())
          .on('data', (row) => {
            products.push(row);
          })
          .on('end', async () => {
            try {
              const importResult = await dbManager.importProductsFromCSV(products);
              resolve(importResult);
            } catch (error) {
              reject(error);
            }
          })
          .on('error', reject);
      });
    }
    
    return { success: false, message: 'Import cancelled' };
  } catch (error) {
    console.error('Error importing products:', error);
    throw error;
  }
});

// Profit analysis IPC handlers
ipcMain.handle('db-get-profit-analysis', async (event, startDate, endDate) => {
  try {
    return await dbManager.getProfitAnalysis(startDate, endDate);
  } catch (error) {
    console.error('Error getting profit analysis:', error);
    throw error;
  }
});

ipcMain.handle('db-get-category-profit-analysis', async (event, startDate, endDate) => {
  try {
    return await dbManager.getCategoryProfitAnalysis(startDate, endDate);
  } catch (error) {
    console.error('Error getting category profit analysis:', error);
    throw error;
  }
});

ipcMain.handle('db-get-inventory-turnover', async () => {
  try {
    return await dbManager.getInventoryTurnoverAnalysis();
  } catch (error) {
    console.error('Error getting inventory turnover:', error);
    throw error;
  }
});

ipcMain.handle('db-get-reorder-analysis', async () => {
  try {
    return await dbManager.getReorderPointAnalysis();
  } catch (error) {
    console.error('Error getting reorder analysis:', error);
    throw error;
  }
});

// PDF Export handler
ipcMain.handle('export-report-pdf', async (event, reportData, reportType) => {
  try {
    const jsPDF = require('jspdf').jsPDF;
    require('jspdf-autotable');
    const { dialog } = require('electron');
    
    const result = await dialog.showSaveDialog(mainWindow, {
      title: `Export ${reportType} Report to PDF`,
      defaultPath: `${reportType}-report-${new Date().toISOString().split('T')[0]}.pdf`,
      filters: [{ name: 'PDF Files', extensions: ['pdf'] }]
    });
    
    if (!result.canceled) {
      const doc = new jsPDF();
      
      // Add title
      doc.setFontSize(20);
      doc.text(`${reportType} Report`, 20, 20);
      
      // Add date
      doc.setFontSize(12);
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, 20, 35);
      
      // Add table based on report type
      if (reportType === 'Profit Analysis') {
        doc.autoTable({
          startY: 50,
          head: [['Product', 'Category', 'Units Sold', 'Revenue', 'Cost', 'Profit', 'Margin %']],
          body: reportData.map(item => [
            item.name,
            item.category || 'N/A',
            item.units_sold,
            `$${item.total_revenue.toFixed(2)}`,
            `$${item.total_cost.toFixed(2)}`,
            `$${item.total_profit.toFixed(2)}`,
            `${item.profit_margin_percent.toFixed(1)}%`
          ])
        });
      }
      
      doc.save(result.filePath);
      return { success: true, filePath: result.filePath };
    }
    
    return { success: false, message: 'Export cancelled' };
  } catch (error) {
    console.error('Error exporting PDF:', error);
    throw error;
  }
});