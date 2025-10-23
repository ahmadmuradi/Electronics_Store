// Manual comprehensive test script for the Electronics Store Inventory App
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

function assertThrows(fn, message) {
  try {
    fn();
    assert(false, `${message} (expected to throw but didn't)`);
  } catch (error) {
    assert(true, `${message} (correctly threw: ${error.message})`);
  }
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

console.log('🧪 Starting Comprehensive Tests for Electronics Store Inventory App\n');

// Test 1: Database Module Loading
console.log('📦 Testing Database Module Loading...');
try {
  const DatabaseManager = require('./database');
  assert(typeof DatabaseManager === 'function', 'DatabaseManager should be a constructor function');
  console.log('✓ Database module loaded successfully\n');
} catch (error) {
  console.log(`✗ Failed to load database module: ${error.message}\n`);
}

// Test 2: Database Initialization
console.log('🗄️  Testing Database Initialization...');
async function testDatabaseInitialization() {
  try {
    // Create test data directory
    const testDataDir = path.join(__dirname, 'test-data');
    if (!fs.existsSync(testDataDir)) {
      fs.mkdirSync(testDataDir, { recursive: true });
    }

    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    
    assertNotNull(dbManager, 'DatabaseManager instance should be created');
    
    // Test initialization
    await dbManager.initialize();
    assert(true, 'Database initialization should complete without errors');
    
    // Test database file creation
    const dbPath = path.join(testDataDir, 'inventory.db');
    assert(fs.existsSync(dbPath), 'Database file should be created');
    
    // Clean up
    await dbManager.close();
    
  } catch (error) {
    assert(false, `Database initialization failed: ${error.message}`);
  }
}

// Test 3: Product CRUD Operations
console.log('📱 Testing Product CRUD Operations...');
async function testProductOperations() {
  try {
    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    await dbManager.initialize();

    // Test Add Product
    const productData = {
      name: 'Test Product',
      description: 'A test product for automated testing',
      price: 99.99,
      cost: 50.00,
      stock_quantity: 100,
      sku: 'TEST001',
      barcode: '1234567890123',
      category: 'Test Category'
    };

    const productId = await dbManager.addProduct(productData);
    assertNotNull(productId, 'Product ID should be returned after adding product');
    assert(typeof productId === 'number', 'Product ID should be a number');

    // Test Get Product
    const retrievedProduct = await dbManager.getProduct(productId);
    assertNotNull(retrievedProduct, 'Product should be retrievable by ID');
    assertEqual(retrievedProduct.name, productData.name, 'Product name should match');
    assertEqual(retrievedProduct.price, productData.price, 'Product price should match');
    assertEqual(retrievedProduct.sku, productData.sku, 'Product SKU should match');

    // Test Update Product
    const updateData = { name: 'Updated Test Product', price: 149.99 };
    await dbManager.updateProduct(productId, updateData);
    const updatedProduct = await dbManager.getProduct(productId);
    assertEqual(updatedProduct.name, updateData.name, 'Product name should be updated');
    assertEqual(updatedProduct.price, updateData.price, 'Product price should be updated');

    // Test Search Products
    const searchResults = await dbManager.searchProducts('Updated');
    assert(searchResults.length > 0, 'Search should return results');
    assert(searchResults.some(p => p.id === productId), 'Search should include updated product');

    // Test Delete Product
    await dbManager.deleteProduct(productId);
    const deletedProduct = await dbManager.getProduct(productId);
    assert(deletedProduct === null, 'Deleted product should not be retrievable');

    await dbManager.close();
    
  } catch (error) {
    assert(false, `Product operations test failed: ${error.message}`);
  }
}

// Test 4: Customer Operations
console.log('👥 Testing Customer Operations...');
async function testCustomerOperations() {
  try {
    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    await dbManager.initialize();

    // Test Add Customer
    const customerData = {
      name: 'John Doe',
      email: 'john@example.com',
      phone: '+1234567890',
      address: '123 Test Street',
      city: 'Test City'
    };

    const customerId = await dbManager.addCustomer(customerData);
    assertNotNull(customerId, 'Customer ID should be returned');

    // Test Get Customer
    const retrievedCustomer = await dbManager.getCustomer(customerId);
    assertNotNull(retrievedCustomer, 'Customer should be retrievable');
    assertEqual(retrievedCustomer.name, customerData.name, 'Customer name should match');
    assertEqual(retrievedCustomer.email, customerData.email, 'Customer email should match');

    // Test Update Loyalty Points
    await dbManager.updateCustomerLoyaltyPoints(customerId, 100);
    const updatedCustomer = await dbManager.getCustomer(customerId);
    assertEqual(updatedCustomer.loyalty_points, 100, 'Loyalty points should be updated');

    await dbManager.close();
    
  } catch (error) {
    assert(false, `Customer operations test failed: ${error.message}`);
  }
}

// Test 5: Sales Processing
console.log('💰 Testing Sales Processing...');
async function testSalesProcessing() {
  try {
    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    await dbManager.initialize();

    // Setup: Add product and customer
    const productId = await dbManager.addProduct({
      name: 'Sales Test Product',
      price: 99.99,
      stock_quantity: 100,
      sku: 'SALES001'
    });

    const customerId = await dbManager.addCustomer({
      name: 'Sales Test Customer',
      email: 'sales@test.com'
    });

    // Test Process Sale
    const saleData = {
      customer_id: customerId,
      total_amount: 199.98,
      tax_amount: 20.00,
      payment_method: 'cash',
      items: [{
        product_id: productId,
        quantity: 2,
        unit_price: 99.99,
        total_price: 199.98
      }]
    };

    const saleId = await dbManager.processSale(saleData);
    assertNotNull(saleId, 'Sale ID should be returned');

    // Verify inventory was updated
    const updatedProduct = await dbManager.getProduct(productId);
    assertEqual(updatedProduct.stock_quantity, 98, 'Product stock should be reduced');

    // Verify customer total spent was updated
    const updatedCustomer = await dbManager.getCustomer(customerId);
    assertEqual(updatedCustomer.total_spent, 199.98, 'Customer total spent should be updated');

    await dbManager.close();
    
  } catch (error) {
    assert(false, `Sales processing test failed: ${error.message}`);
  }
}

// Test 6: Inventory Management
console.log('📦 Testing Inventory Management...');
async function testInventoryManagement() {
  try {
    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    await dbManager.initialize();

    // Add test products with different stock levels
    const lowStockProductId = await dbManager.addProduct({
      name: 'Low Stock Product',
      price: 99.99,
      stock_quantity: 5,
      min_stock_level: 10,
      sku: 'LOW001'
    });

    const normalStockProductId = await dbManager.addProduct({
      name: 'Normal Stock Product',
      price: 149.99,
      stock_quantity: 50,
      min_stock_level: 10,
      sku: 'NORM001'
    });

    // Test Low Stock Detection
    const lowStockProducts = await dbManager.getLowStockProducts();
    assert(lowStockProducts.length > 0, 'Should detect low stock products');
    assert(lowStockProducts.some(p => p.id === lowStockProductId), 'Should include low stock product');
    assert(!lowStockProducts.some(p => p.id === normalStockProductId), 'Should not include normal stock product');

    // Test Inventory Adjustment
    await dbManager.adjustInventory(normalStockProductId, -10, 'Test adjustment');
    const adjustedProduct = await dbManager.getProduct(normalStockProductId);
    assertEqual(adjustedProduct.stock_quantity, 40, 'Stock should be adjusted correctly');

    await dbManager.close();
    
  } catch (error) {
    assert(false, `Inventory management test failed: ${error.message}`);
  }
}

// Test 7: Error Handling
console.log('⚠️  Testing Error Handling...');
async function testErrorHandling() {
  try {
    const DatabaseManager = require('./database');
    const dbManager = new DatabaseManager();
    await dbManager.initialize();

    // Test duplicate SKU
    const productData1 = { name: 'Product 1', price: 99.99, stock_quantity: 50, sku: 'DUP001' };
    const productData2 = { name: 'Product 2', price: 149.99, stock_quantity: 30, sku: 'DUP001' };

    await dbManager.addProduct(productData1);
    
    await assertThrowsAsync(
      () => dbManager.addProduct(productData2),
      'Should throw error for duplicate SKU'
    );

    // Test invalid product ID
    const nonExistentProduct = await dbManager.getProduct(99999);
    assert(nonExistentProduct === null, 'Should return null for non-existent product');

    await dbManager.close();
    
  } catch (error) {
    assert(false, `Error handling test failed: ${error.message}`);
  }
}

// Test 8: File System Operations
console.log('📁 Testing File System Operations...');
function testFileSystemOperations() {
  try {
    // Test main application files exist
    const mainFiles = ['main.js', 'database.js', 'renderer.js', 'index.html', 'package.json'];
    
    mainFiles.forEach(file => {
      const filePath = path.join(__dirname, file);
      assert(fs.existsSync(filePath), `${file} should exist`);
    });

    // Test package.json structure
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
    assertNotNull(packageJson.name, 'Package should have a name');
    assertNotNull(packageJson.version, 'Package should have a version');
    assertNotNull(packageJson.main, 'Package should have a main entry point');
    
  } catch (error) {
    assert(false, `File system operations test failed: ${error.message}`);
  }
}

// Test 9: Configuration and Dependencies
console.log('⚙️  Testing Configuration and Dependencies...');
function testConfigurationAndDependencies() {
  try {
    const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));
    
    // Test essential dependencies
    const requiredDeps = ['chart.js', 'jsbarcode', 'qrcode', 'uuid', 'jspdf', 'xlsx'];
    requiredDeps.forEach(dep => {
      assert(packageJson.dependencies && packageJson.dependencies[dep], `Should have ${dep} dependency`);
    });

    // Test dev dependencies
    const requiredDevDeps = ['electron', 'electron-builder'];
    requiredDevDeps.forEach(dep => {
      assert(packageJson.devDependencies && packageJson.devDependencies[dep], `Should have ${dep} dev dependency`);
    });

    // Test scripts
    const requiredScripts = ['start', 'build', 'test'];
    requiredScripts.forEach(script => {
      assert(packageJson.scripts && packageJson.scripts[script], `Should have ${script} script`);
    });
    
  } catch (error) {
    assert(false, `Configuration test failed: ${error.message}`);
  }
}

// Run All Tests
async function runAllTests() {
  console.log('🚀 Running all tests...\n');
  
  // File system and configuration tests (synchronous)
  testFileSystemOperations();
  testConfigurationAndDependencies();
  
  // Database tests (asynchronous)
  await testDatabaseInitialization();
  await testProductOperations();
  await testCustomerOperations();
  await testSalesProcessing();
  await testInventoryManagement();
  await testErrorHandling();
  
  // Generate Test Report
  console.log('\n📊 TEST RESULTS SUMMARY');
  console.log('========================');
  console.log(`Total Tests: ${testResults.total}`);
  console.log(`Passed: ${testResults.passed} ✓`);
  console.log(`Failed: ${testResults.failed} ✗`);
  console.log(`Success Rate: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
  
  if (testResults.failed > 0) {
    console.log('\n❌ FAILED TESTS:');
    testResults.details
      .filter(test => test.status === 'FAIL')
      .forEach(test => console.log(`  - ${test.message}`));
  }
  
  console.log('\n✅ Test execution completed!');
  
  // Clean up test data
  const testDataDir = path.join(__dirname, 'test-data');
  if (fs.existsSync(testDataDir)) {
    fs.rmSync(testDataDir, { recursive: true, force: true });
    console.log('🧹 Test data cleaned up');
  }
  
  return testResults;
}

// Execute tests if run directly
if (require.main === module) {
  runAllTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = { runAllTests, testResults };
