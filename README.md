# Electronics Store Inventory Management

A modern, feature-rich desktop application for managing electronics store inventory, built with Electron and SQLite.

## ✨ Features

### 🎨 Modern UI/UX
- **Beautiful gradient design** with glassmorphism effects
- **Responsive layout** that works on different screen sizes
- **Smooth animations** and transitions
- **Dark theme-ready** design system
- **Professional typography** and spacing

### 📊 Advanced Analytics Dashboard
- **Real-time metrics cards** showing key business indicators
- **Interactive charts** using Chart.js:
  - Top-selling products (doughnut chart)
  - Sales trend analysis (line chart)
- **Low stock alerts** with visual indicators
- **Recent sales tracking** with detailed tables

### 💾 Local Database Integration
- **SQLite database** for offline functionality
- **Hybrid online/offline** operation
- **Data persistence** across app sessions
- **Automatic data synchronization** when online
- **Backup and restore** capabilities

### 🔧 Enhanced Functionality
- **Form validation** with real-time feedback
- **Error handling** with user-friendly messages
- **Toast notifications** for all actions
- **Keyboard shortcuts** for power users
- **Application menu** with common actions

### 🛡️ Security & Performance
- **Context isolation** for security
- **Preload scripts** for safe IPC communication
- **Optimized database queries**
- **Memory-efficient operations**

## 🚀 Installation

### Prerequisites
- Node.js 16.0.0 or higher
- npm or yarn package manager

### Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd e:\ElectronicsStore\electronics-store-app\desktop\electron-inventory-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the application:**
   ```bash
   npm start
   ```

### Development Mode
```bash
npm run dev
```
This starts the app with developer tools enabled.

## 📖 Usage Guide

### Getting Started
1. **Launch the application** using `npm start`
2. **Add your first product** using the "Add New Product" form
3. **View inventory** in the main inventory section
4. **Check analytics** by switching to the Reports tab

### Key Features

#### Product Management
- **Add Products**: Fill out the form with name, price, stock quantity, SKU, and description
- **Edit Products**: Click the "Edit" button on any product to modify its details
- **Delete Products**: Click the "Delete" button (with confirmation dialog)
- **View Details**: See all product information in an organized card layout

#### Sales Management
- **Create Sales**: Use the sales form to record transactions
- **Multiple Items**: Add multiple products to a single sale
- **Automatic Stock Updates**: Stock levels automatically decrease with sales
- **Sales History**: View all sales in the Reports section

#### Analytics Dashboard
- **Metrics Overview**: See total products, low stock items, sales count, and revenue
- **Visual Charts**: Interactive charts showing top products and sales trends
- **Low Stock Alerts**: Immediate visibility of products needing restocking
- **Sales Reports**: Detailed tables of recent transactions

### Keyboard Shortcuts
- **Ctrl/Cmd + N**: Focus on new product form
- **Ctrl/Cmd + 1**: Switch to Inventory tab
- **Ctrl/Cmd + 2**: Switch to Reports tab
- **Ctrl/Cmd + R**: Reload application
- **F12**: Toggle Developer Tools

## 🏗️ Architecture

### Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Node.js, Electron
- **Database**: SQLite3
- **Charts**: Chart.js
- **UI Framework**: Custom CSS with modern design patterns

### File Structure
```
electron-inventory-app/
├── main.js              # Main Electron process
├── preload.js           # Secure IPC bridge
├── database.js          # SQLite database manager
├── renderer.js          # Frontend application logic
├── index.html           # Main application UI
├── styles.css           # Modern CSS styling
├── package.json         # Dependencies and scripts
└── README.md           # This file
```

### Database Schema
- **products**: Product information and inventory
- **sales**: Sales transaction records
- **sale_items**: Individual items within sales
- **settings**: Application configuration

## 🔧 Configuration

### Database Location
The SQLite database is stored in the user's data directory:
- **Windows**: `%APPDATA%/electron-inventory-app/inventory.db`
- **macOS**: `~/Library/Application Support/electron-inventory-app/inventory.db`
- **Linux**: `~/.config/electron-inventory-app/inventory.db`

### Settings
Application settings are stored in the database and can be modified:
- API base URL for server synchronization
- Low stock threshold (default: 10)
- Currency symbol (default: $)
- Sync enabled/disabled

## 🚀 Building for Production

### Create Executable
```bash
npm run build
```

This creates platform-specific executables in the `dist/` directory.

### Supported Platforms
- Windows (x64)
- macOS (x64, arm64)
- Linux (x64)

## 🔄 Data Synchronization

The application supports hybrid online/offline operation:

1. **Offline Mode**: All data is stored locally in SQLite
2. **Online Mode**: Attempts to sync with backend server
3. **Automatic Sync**: Syncs when connection is restored
4. **Conflict Resolution**: Handles data conflicts gracefully

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
- Ensure the app has write permissions to the user data directory
- Check if SQLite3 is properly installed

**Chart Display Issues**
- Verify Chart.js is loaded from CDN
- Check browser console for JavaScript errors

**Sync Problems**
- Confirm backend server is running on http://localhost:8000
- Check network connectivity
- Review console logs for sync errors

### Debug Mode
Run with debug logging:
```bash
DEBUG=* npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review console logs for errors
- Create an issue in the repository

---

**Built with ❤️ for modern electronics store management**
