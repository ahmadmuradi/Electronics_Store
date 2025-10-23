// Simple test to check if Electron is working
console.log('Testing Electron import...');

try {
  const { app, BrowserWindow } = require('electron');
  console.log('Electron imported successfully');
  console.log('App object:', typeof app);
  console.log('App methods:', Object.getOwnPropertyNames(app).slice(0, 10));
  
  if (app && app.whenReady) {
    console.log('✅ app.whenReady is available');
  } else {
    console.log('❌ app.whenReady is NOT available');
  }
} catch (error) {
  console.error('❌ Error importing Electron:', error.message);
}
