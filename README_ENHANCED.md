# Enhanced Electronics Store Inventory Management System

A comprehensive, AI-powered inventory management system designed specifically for electronics stores with advanced features including multi-location tracking, demand forecasting, automated reordering, and cloud integrations.

## 🚀 Features Implemented

### ✅ Priority 1: Core Inventory Features

- **Multi-location inventory tracking** - Track stock across multiple store locations and warehouses
- **Automated reorder notifications** - AI-powered alerts with email notifications when stock runs low
- **Batch/serial number tracking** - Complete traceability for electronics with batch and serial number support

### ✅ Priority 2: Security & Multi-User

- **User authentication system** - JWT-based authentication with secure password hashing
- **Role-based permissions** - Three user roles (Admin, Manager, Cashier) with appropriate access controls
- **Audit logging** - Complete audit trail for all operations and changes

### ✅ Priority 3: Cloud & Integration

- **Cloud backup functionality** - Automated database backups to AWS S3 with restore capabilities
- **QuickBooks integration** - Sync customers and sales data with QuickBooks Online
- **Email notifications system** - Comprehensive email alerts for low stock, sales reports, and system events

### ✅ Priority 4: AI & Automation

- **Demand forecasting** - Machine learning models predict future demand based on sales patterns
- **Automatic reorder suggestions** - AI-powered recommendations for optimal reorder points and quantities
- **Price optimization algorithms** - Dynamic pricing suggestions based on demand elasticity analysis

## 📋 System Requirements

- **Python 3.8+**
- **Node.js 14+** (for Electron desktop app)
- **SQLite** (default) or **PostgreSQL/MySQL** (production)
- **4GB RAM minimum** (8GB recommended for AI features)
- **2GB disk space** (for models and backups)

## 🛠️ Installation & Setup

### Backend Setup

1. **Navigate to backend directory:**

   ```bash
   cd electronics-store-app/backend
   ```

2. **Run the enhanced startup script:**

   ```bash
   python start_enhanced_server.py
   ```

   This script will automatically:
   - Check Python version compatibility
   - Install all required packages
   - Set up environment variables
   - Create necessary directories
   - Initialize the database with sample data
   - Start the FastAPI server

3. **Access the API documentation:**
   - Open <http://localhost:8001/docs> in your browser
   - Interactive API documentation with all endpoints

### Desktop App Setup

1. **Navigate to desktop app directory:**

   ```bash
   cd electronics-store-app/desktop/electron-inventory-app
   ```

2. **Open the enhanced interface:**
   - Open `enhanced-index.html` in your browser, or
   - Use the existing Electron app with enhanced features

### Default User Accounts

The system creates three default user accounts:

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | Admin | Full system access, user management, AI analytics |
| manager | manager123 | Manager | Inventory management, reports, reorder alerts |
| cashier | cashier123 | Cashier | Sales processing, basic inventory viewing |

**⚠️ Important:** Change these default passwords in production!

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory with your configuration:

```env
# Database
DATABASE_URL=sqlite:///./enhanced_inventory.db

# Security
SECRET_KEY=your-super-secret-key-change-this

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourstore.com
COMPANY_NAME=Your Electronics Store

# AWS Configuration (for cloud backup)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
BACKUP_BUCKET_NAME=your-backup-bucket

# QuickBooks Integration
QUICKBOOKS_CLIENT_ID=your-quickbooks-client-id
QUICKBOOKS_CLIENT_SECRET=your-quickbooks-client-secret
QUICKBOOKS_REDIRECT_URI=http://localhost:8001/auth/quickbooks/callback
```

### Email Setup (Gmail Example)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password in `SMTP_PASSWORD`

### AWS S3 Setup (for Cloud Backup)

1. Create an AWS account and S3 bucket
2. Create IAM user with S3 permissions
3. Add credentials to environment variables

## 📊 API Endpoints

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Inventory Management

- `GET /products/` - List all products
- `POST /products/` - Create new product
- `PUT /products/{id}` - Update product
- `GET /products/{id}/locations` - Get product stock by location
- `PUT /product-locations/{product_id}/{location_id}/stock` - Update stock

### Multi-Location Support

- `GET /locations/` - List all locations
- `POST /locations/` - Create new location
- `POST /product-locations/` - Add product to location

### Batch/Serial Tracking

- `POST /batch-serials/` - Create batch/serial entry
- `GET /products/{id}/batch-serials` - Get product batch/serial numbers

### AI Analytics

- `GET /analytics/demand-forecast/{product_id}` - Get demand forecast
- `POST /analytics/train-demand-model/{product_id}` - Train AI model
- `GET /analytics/price-optimization/{product_id}` - Get price suggestions
- `GET /analytics/reorder-suggestions` - Get AI reorder recommendations

### Cloud & Integrations

- `POST /cloud/backup/create` - Create database backup
- `GET /cloud/backup/list` - List available backups
- `POST /cloud/backup/restore` - Restore from backup
- `GET /integrations/quickbooks/auth-url` - Get QuickBooks auth URL
- `POST /integrations/quickbooks/sync-customers` - Sync to QuickBooks

### Notifications

- `POST /notifications/send-low-stock-alert` - Send low stock email
- `POST /notifications/send-sales-report` - Send sales report email

## 🤖 AI Features

### Demand Forecasting

The system uses machine learning to predict future demand:

- **Random Forest** and **Gradient Boosting** models
- **Time-series features**: seasonality, trends, lag variables
- **External factors**: price changes, promotions
- **Accuracy metrics**: Mean Absolute Error (MAE) tracking

**Usage:**

```python
# Train model for a product
POST /analytics/train-demand-model/123

# Get 30-day forecast
GET /analytics/demand-forecast/123?days_ahead=30
```

### Price Optimization

AI-powered pricing recommendations:

- **Price elasticity analysis** using log-log regression
- **Profit maximization** algorithms
- **Market positioning** suggestions
- **Competitive pricing** insights

### Automated Reordering

Smart reorder point calculations:

- **Economic Order Quantity (EOQ)** optimization
- **Safety stock** calculations with service level targets
- **Lead time** variability analysis
- **Seasonal adjustment** factors

## 🔒 Security Features

### Authentication & Authorization

- **JWT tokens** with expiration
- **Bcrypt password hashing**
- **Role-based access control** (RBAC)
- **Session management**

### Data Protection

- **SQL injection** prevention with parameterized queries
- **Input validation** using Pydantic models
- **CORS protection** with configurable origins
- **Audit logging** for compliance

### Best Practices

- **Environment variable** configuration
- **Secure defaults** for all settings
- **Password complexity** requirements
- **Regular security updates**

## 📈 Monitoring & Analytics

### Built-in Dashboards

- **Real-time inventory** levels across locations
- **Sales performance** metrics and trends
- **Low stock alerts** with priority scoring
- **AI model performance** tracking

### Reporting Features

- **Automated email reports** (daily, weekly, monthly)
- **Custom date ranges** for analysis
- **Export capabilities** (CSV, PDF)
- **Integration** with business intelligence tools

## 🚀 Deployment

### Development Environment

```bash
# Start development server
python start_enhanced_server.py

# Access at http://localhost:8001
```

### Production Deployment

1. **Use production database:**

   ```env
   DATABASE_URL=postgresql://user:password@localhost/inventory_db
   ```

2. **Configure reverse proxy (Nginx):**

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Use process manager (systemd/supervisor):**

   ```ini
   [program:inventory-api]
   command=python -m uvicorn enhanced_main:app --host 0.0.0.0 --port 8001
   directory=/path/to/backend
   user=inventory
   autostart=true
   autorestart=true
   ```

4. **Set up SSL certificate:**

   ```bash
   certbot --nginx -d your-domain.com
   ```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest test_enhanced_main.py -v

# Run with coverage
pytest --cov=enhanced_main test_enhanced_main.py
```

### Test Coverage

- **Authentication** endpoints
- **CRUD operations** for all entities
- **AI analytics** functions
- **Cloud integrations** (mocked)
- **Email notifications** (mocked)

## 🔧 Troubleshooting

### Common Issues

1. **Database connection errors:**

   ```bash
   # Check database URL
   echo $DATABASE_URL
   
   # Recreate database
   rm enhanced_inventory.db
   python start_enhanced_server.py
   ```

2. **Email not sending:**

   ```bash
   # Check SMTP configuration
   python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
   ```

3. **AI models not training:**

   ```bash
   # Check data availability
   # Ensure at least 30 days of sales data exists
   ```

4. **Cloud backup failing:**

   ```bash
   # Verify AWS credentials
   aws s3 ls s3://your-backup-bucket
   ```

### Performance Optimization

1. **Database indexing:**
   - Product SKU/UPC fields are indexed
   - Foreign keys have automatic indexes
   - Consider composite indexes for frequent queries

2. **AI model caching:**
   - Models are cached in memory after training
   - Periodic retraining recommended (weekly)

3. **Background tasks:**
   - Use Celery for heavy operations in production
   - Configure Redis for task queue

## 📞 Support & Contributing

### Getting Help

- **Documentation:** Check this README and API docs
- **Issues:** Create GitHub issues for bugs
- **Questions:** Use GitHub discussions

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

### Roadmap

- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] Multi-currency support
- [ ] Barcode scanning integration
- [ ] Supplier portal
- [ ] Advanced reporting engine

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SQLAlchemy** for robust database ORM
- **Scikit-learn** for machine learning capabilities
- **Electron** for cross-platform desktop apps
- **Chart.js** for beautiful data visualizations

---

**Built with ❤️ for electronics store owners who want to leverage AI and automation to grow their business.**
