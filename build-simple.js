const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Building Electronics Store Desktop App...');

// Create a simple build directory
const buildDir = path.join(__dirname, 'build');
if (!fs.existsSync(buildDir)) {
    fs.mkdirSync(buildDir);
}

// Copy main application files
const filesToCopy = [
    'main.js',
    'enhanced-index.html',
    'enhanced-renderer.js',
    'preload.js',
    'styles.css',
    'database.js',
    'package.json'
];

console.log('📁 Copying application files...');
filesToCopy.forEach(file => {
    if (fs.existsSync(file)) {
        fs.copyFileSync(file, path.join(buildDir, file));
        console.log(`✅ Copied ${file}`);
    }
});

// Copy node_modules (essential ones only)
console.log('📦 Copying essential dependencies...');
const nodeModulesSource = path.join(__dirname, 'node_modules');
const nodeModulesDest = path.join(buildDir, 'node_modules');

if (fs.existsSync(nodeModulesSource)) {
    // Create a simple copy of essential modules
    const essentialModules = ['chart.js', 'qrcode', 'jspdf', 'uuid', 'xlsx'];
    
    if (!fs.existsSync(nodeModulesDest)) {
        fs.mkdirSync(nodeModulesDest);
    }
    
    essentialModules.forEach(module => {
        const sourcePath = path.join(nodeModulesSource, module);
        const destPath = path.join(nodeModulesDest, module);
        
        if (fs.existsSync(sourcePath)) {
            try {
                execSync(`xcopy "${sourcePath}" "${destPath}" /E /I /Q`, { stdio: 'inherit' });
                console.log(`✅ Copied ${module}`);
            } catch (error) {
                console.log(`⚠️  Could not copy ${module}: ${error.message}`);
            }
        }
    });
}

// Create a startup script
const startupScript = `@echo off
echo Starting Electronics Store Inventory...
echo.
echo 📊 Dashboard: http://localhost:8001/dashboard
echo 📚 API Docs: http://localhost:8001/docs
echo.
node main.js
pause`;

fs.writeFileSync(path.join(buildDir, 'start.bat'), startupScript);

// Create a README for the build
const buildReadme = `# Electronics Store Desktop Application

## Quick Start
1. Double-click 'start.bat' to launch the application
2. The application will start and open your default browser
3. Access the dashboard at: http://localhost:8001/dashboard

## Default Login Credentials
- Admin: admin / admin123
- Manager: manager / manager123  
- Cashier: cashier / cashier123

## Features
- Inventory Management
- Barcode Generation
- Sales Reporting
- Multi-location Support
- User Management

Built with Electron and Node.js
`;

fs.writeFileSync(path.join(buildDir, 'README.txt'), buildReadme);

console.log('');
console.log('🎉 Build completed successfully!');
console.log(`📁 Build location: ${buildDir}`);
console.log('');
console.log('To run the application:');
console.log('1. Navigate to the build folder');
console.log('2. Double-click start.bat');
console.log('');
