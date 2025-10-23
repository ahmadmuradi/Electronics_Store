// Corrected comprehensive test script for the Electronics Store Inventory App
const path = require('path');
const fs = require('fs');

// Test Results Storage
const testResults = {
  passed: 0,
  failed: 0,
  total: 0,
  details: []
};

// Test Helper Functions
function assert(condition, message) {
  testResults.total++;
  if (condition) {
    testResults.passed++;
    console.log(`✓ ${message}`);
    testResults.details.push({ status: 'PASS', message });
  } else {
    testResults.failed++;
    console.log(`✗ ${message}`);
    testResults.details.push({ status: 'FAIL', message });
  }
}

function assertEqual(actual, expected, message) {
  const condition = actual === expected;
  assert(condition, `${message} (expected: ${expected}, actual: ${actual})`);
}

function assertNotNull(value, message) {
  assert(value !== null && value !== undefined, message);
}

async function assertThrowsAsync(fn, message) {
  try {
    await fn();
    assert(false, `${message} (expected to throw but didn't)`);
  } catch (error) {
    assert(true, `${message} (correctly threw: ${error.message})`);
  }
}

// Mock Electron for testing
const mockElectron = {
  app: {
    getPath: (name) => {
      if (name === 'userData') {
        return path.join(__dirname, 'test-data');
      }
      return '/tmp';
    }
  }
};

// Replace electron module for testing
require.cache[require.resolve('electron')] = {
  exports: mockElectron
};

console.log('🧪 Starting Corrected Comprehensive Tests\n');

// Test Database Operations with Correct Method Names
async function testCorrectedDatabaseOperations() {
  console.log('🗄️  Testing Database Operations with Correct Methods...');
  
  try {
    // Create test data directory
    const testDataDir = path.join(__dirname, 'test-data');
    if (!fs.existsSync(testDataDir)) {
      fs.mkdirSync(testDataDir, { recursive: true });
    }

    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    
    // Test initialization
    await dbManager.initialize();
    assert(true, 'Database initialization completed successfully');

    // Test Product Operations
    console.log('\n📱 Testing Product CRUD Operations...');
    
    // Add Product
    const productData = {
      name: 'Test Product',
      description: 'A test product',
      price: 99.99,
      stock_quantity: 100,
      sku: 'TEST001'
    };

    const productResult = await dbManager.addProduct(productData);
    assertNotNull(productResult, 'Product should be added successfully');
    
    // Get all products to find our added product
    const allProducts = await dbManager.getProducts();
    assert(allProducts.length > 0, 'Should retrieve products list');
    
    const addedProduct = allProducts.find(p => p.sku === 'TEST001');
    assertNotNull(addedProduct, 'Added product should be found in products list');
    assertEqual(addedProduct.name, productData.name, 'Product name should match');
    
    // Update Product
    await dbManager.updateProduct(addedProduct.id, { 
      name: 'Updated Test Product', 
      price: 149.99, 
      stock_quantity: 90 
    });
    
    const updatedProduct = await dbManager.getProduct(addedProduct.id);
    assertEqual(updatedProduct.name, 'Updated Test Product', 'Product name should be updated');
    assertEqual(updatedProduct.price, 149.99, 'Product price should be updated');

    // Test Customer Operations
    console.log('\n👥 Testing Customer Operations...');
    
    const customerData = {
      name: 'John Doe',
      email: 'john@example.com',
      phone: '+1234567890',
      address: '123 Test Street',
      city: 'Test City',
      postal_code: '12345'
    };

    const customerResult = await dbManager.addCustomer(customerData);
    assertNotNull(customerResult, 'Customer should be added successfully');
    
    const allCustomers = await dbManager.getCustomers();
    const addedCustomer = allCustomers.find(c => c.email === 'john@example.com');
    assertNotNull(addedCustomer, 'Added customer should be found');
    assertEqual(addedCustomer.name, customerData.name, 'Customer name should match');

    // Test Supplier Operations
    console.log('\n🏪 Testing Supplier Operations...');
    
    const supplierData = {
      name: 'Test Supplier Inc',
      contact_person: 'Jane Smith',
      email: 'jane@testsupplier.com',
      phone: '+1987654321',
      address: '456 Supplier Ave',
      city: 'Supplier City',
      country: 'USA'
    };

    const supplierResult = await dbManager.addSupplier(supplierData);
    assertNotNull(supplierResult, 'Supplier should be added successfully');
    
    const allSuppliers = await dbManager.getSuppliers();
    const addedSupplier = allSuppliers.find(s => s.email === 'jane@testsupplier.com');
    assertNotNull(addedSupplier, 'Added supplier should be found');
    assertEqual(addedSupplier.name, supplierData.name, 'Supplier name should match');

    // Test Sales Operations
    console.log('\n💰 Testing Sales Operations...');
    
    const saleData = {
      customer_id: addedCustomer.id,
      total_amount: 199.98,
      tax_amount: 20.00,
      payment_method: 'cash',
      items: [{
        product_id: addedProduct.id,
        quantity: 2,
        unit_price: 99.99,
        total_price: 199.98
      }]
    };

    const saleResult = await dbManager.addSale(saleData);
    assertNotNull(saleResult, 'Sale should be processed successfully');
    
    // Verify inventory was updated
    const productAfterSale = await dbManager.getProduct(addedProduct.id);
    assertEqual(productAfterSale.stock_quantity, 88, 'Product stock should be reduced by sale quantity');

    // Test Low Stock Detection
    console.log('\n📦 Testing Low Stock Detection...');
    
    // Add a low stock product
    const lowStockProduct = {
      name: 'Low Stock Product',
      price: 50.00,
      stock_quantity: 5,
      sku: 'LOW001'
    };
    
    await dbManager.addProduct(lowStockProduct);
    
    const lowStockProducts = await dbManager.getLowStockProducts(10);
    assert(lowStockProducts.length > 0, 'Should detect low stock products');
    
    const foundLowStock = lowStockProducts.find(p => p.sku === 'LOW001');
    assertNotNull(foundLowStock, 'Low stock product should be detected');

    // Test Analytics and Reporting
    console.log('\n📊 Testing Analytics and Reporting...');
    
    const topSellingProducts = await dbManager.getTopSellingProducts(5);
    assert(Array.isArray(topSellingProducts), 'Should return top selling products array');
    
    const salesReport = await dbManager.getSalesReport('2024-01-01', '2024-12-31');
    assert(Array.isArray(salesReport), 'Should return sales report array');

    // Test Settings Operations
    console.log('\n⚙️  Testing Settings Operations...');
    
    await dbManager.setSetting('test_setting', 'test_value');
    const retrievedSetting = await dbManager.getSetting('test_setting');
    assertEqual(retrievedSetting, 'test_value', 'Setting should be stored and retrieved correctly');

    // Test Export Operations
    console.log('\n📤 Testing Export Operations...');
    
    const exportedProducts = await dbManager.exportProductsToCSV();
    assert(Array.isArray(exportedProducts), 'Should export products to CSV format');
    assert(exportedProducts.length > 0, 'Exported products should contain data');

    // Test Error Handling
    console.log('\n⚠️  Testing Error Handling...');
    
    // Test duplicate SKU
    const duplicateProduct = {
      name: 'Duplicate Product',
      price: 75.00,
      stock_quantity: 25,
      sku: 'TEST001' // Same SKU as first product
    };
    
    await assertThrowsAsync(
      () => dbManager.addProduct(duplicateProduct),
      'Should throw error for duplicate SKU'
    );

    // Test invalid product ID
    const nonExistentProduct = await dbManager.getProduct(99999);
    assert(nonExistentProduct === null, 'Should return null for non-existent product');

    // Clean up
    await dbManager.close();
    
    console.log('\n✅ All database operations tested successfully!');
    
  } catch (error) {
    assert(false, `Database operations test failed: ${error.message}`);
    console.error('Full error:', error);
  }
}

// Test Application Files and Structure
function testApplicationStructure() {
  console.log('\n📁 Testing Application Structure...');
  
  const requiredFiles = [
    'main.js',
    'database.js', 
    'renderer.js',
    'index.html',
    'package.json',
    'preload.js',
    'styles.css'
  ];
  
  requiredFiles.forEach(file => {
    const filePath = path.join(__dirname, file);
    assert(fs.existsSync(filePath), `${file} should exist`);
  });

  // Test package.json structure
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
  assertNotNull(packageJson.name, 'Package should have a name');
  assertNotNull(packageJson.version, 'Package should have a version');
  assertNotNull(packageJson.main, 'Package should have a main entry point');
  
  // Test essential dependencies
  const requiredDeps = ['chart.js', 'jsbarcode', 'qrcode', 'uuid', 'jspdf', 'xlsx'];
  requiredDeps.forEach(dep => {
    assert(packageJson.dependencies && packageJson.dependencies[dep], `Should have ${dep} dependency`);
  });

  // Test scripts
  const requiredScripts = ['start', 'build', 'test'];
  requiredScripts.forEach(script => {
    assert(packageJson.scripts && packageJson.scripts[script], `Should have ${script} script`);
  });
}

// Test Application Startup (without actually starting Electron)
function testApplicationStartup() {
  console.log('\n🚀 Testing Application Startup Logic...');
  
  try {
    // Test main.js can be loaded (syntax check)
    const mainContent = fs.readFileSync(path.join(__dirname, 'main.js'), 'utf8');
    assert(mainContent.includes('createWindow'), 'main.js should contain createWindow function');
    assert(mainContent.includes('BrowserWindow'), 'main.js should use BrowserWindow');
    assert(mainContent.includes('app.whenReady'), 'main.js should handle app ready event');
    
    // Test renderer.js can be loaded
    const rendererContent = fs.readFileSync(path.join(__dirname, 'renderer.js'), 'utf8');
    assert(rendererContent.includes('electronAPI'), 'renderer.js should use electronAPI');
    
    // Test preload.js structure
    const preloadContent = fs.readFileSync(path.join(__dirname, 'preload.js'), 'utf8');
    assert(preloadContent.includes('contextBridge'), 'preload.js should use contextBridge');
    assert(preloadContent.includes('ipcRenderer'), 'preload.js should use ipcRenderer');
    
  } catch (error) {
    assert(false, `Application startup test failed: ${error.message}`);
  }
}

// Test UI Components (static analysis)
function testUIComponents() {
  console.log('\n🎨 Testing UI Components...');
  
  try {
    const htmlContent = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
    
    // Test essential UI elements
    assert(htmlContent.includes('products-section'), 'Should have products section');
    assert(htmlContent.includes('customers-section'), 'Should have customers section');
    assert(htmlContent.includes('sales-section'), 'Should have sales section');
    assert(htmlContent.includes('reports-section'), 'Should have reports section');
    
    // Test CSS file
    const cssContent = fs.readFileSync(path.join(__dirname, 'styles.css'), 'utf8');
    assert(cssContent.length > 1000, 'CSS file should contain substantial styling');
    
  } catch (error) {
    assert(false, `UI components test failed: ${error.message}`);
  }
}

// Run All Tests
async function runAllTests() {
  console.log('🚀 Running all corrected tests...\n');
  
  // Structure and file tests
  testApplicationStructure();
  testApplicationStartup();
  testUIComponents();
  
  // Database functionality tests
  await testCorrectedDatabaseOperations();
  
  // Generate Test Report
  console.log('\n📊 FINAL TEST RESULTS');
  console.log('======================');
  console.log(`Total Tests: ${testResults.total}`);
  console.log(`Passed: ${testResults.passed} ✅`);
  console.log(`Failed: ${testResults.failed} ❌`);
  console.log(`Success Rate: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
  
  if (testResults.failed > 0) {
    console.log('\n❌ FAILED TESTS:');
    testResults.details
      .filter(test => test.status === 'FAIL')
      .forEach(test => console.log(`  - ${test.message}`));
  } else {
    console.log('\n🎉 ALL TESTS PASSED! The application is working correctly.');
  }
  
  // Performance Summary
  const performanceGrade = testResults.passed / testResults.total;
  let grade = 'F';
  if (performanceGrade >= 0.9) grade = 'A';
  else if (performanceGrade >= 0.8) grade = 'B';
  else if (performanceGrade >= 0.7) grade = 'C';
  else if (performanceGrade >= 0.6) grade = 'D';
  
  console.log(`\n📈 Application Health Grade: ${grade}`);
  
  // Clean up test data
  const testDataDir = path.join(__dirname, 'test-data');
  if (fs.existsSync(testDataDir)) {
    try {
      // Wait a bit for database to fully close
      setTimeout(() => {
        fs.rmSync(testDataDir, { recursive: true, force: true });
        console.log('🧹 Test data cleaned up');
      }, 1000);
    } catch (error) {
      console.log('⚠️  Could not clean up test data (database may still be in use)');
    }
  }
  
  return testResults;
}

// Execute tests if run directly
if (require.main === module) {
  runAllTests().catch(error => {
    console.error('❌ Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = { runAllTests, testResults };
