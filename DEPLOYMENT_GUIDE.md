# Electronics Store Inventory System - Deployment Guide

## 🚀 Quick Start (Development)

### Prerequisites

- **Python 3.8+** (tested with Python 3.14)
- **Node.js 16+** (for desktop and mobile apps)
- **Git** (for version control)

### 1. Backend Setup (Required)

```bash
# Navigate to backend directory
cd electronics-store-app/backend

# Install dependencies
pip install -r requirements_core.txt

# Copy environment template
copy .env.example .env

# Start the server
python start_enhanced_server.py
```

The server will start on `http://localhost:8001`

- **API Documentation**: <http://localhost:8001/docs>
- **Default Admin**: username: `admin`, password: `admin123`

### 2. Desktop App Setup (Optional)

```bash
# Navigate to desktop app
cd electronics-store-app/desktop/electron-inventory-app

# Install dependencies
npm install

# Start the desktop app
npm start
```

### 3. Mobile App Setup (Optional)

```bash
# Navigate to mobile app
cd electronics-store-app/electronics-mobile-app

# Install dependencies
npm install

# Start with Expo
npx expo start
```

## 🐳 Production Deployment with Docker

### Prerequisites

- **Docker** and **Docker Compose**
- **Domain name** (for SSL)

### 1. Environment Configuration

Create `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://inventory_user:inventory_pass@postgres:5432/inventory_db

# Security
SECRET_KEY=your-super-secret-production-key

# Email (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
COMPANY_NAME=Your Electronics Store

# AWS (for backups)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
BACKUP_BUCKET_NAME=your-backup-bucket

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password
```

### 2. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f inventory-api
```

### 3. Access Services

- **Main API**: <http://localhost:8001>
- **Web Interface**: <http://localhost> (via Nginx)
- **Grafana Monitoring**: <http://localhost:3000>
- **Prometheus Metrics**: <http://localhost:9090>

## 🔧 Configuration Options

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | SQLite file |
| `SECRET_KEY` | JWT secret key | Change in production! |
| `SMTP_*` | Email configuration | Gmail settings |
| `AWS_*` | AWS credentials for backups | Optional |
| `REDIS_URL` | Redis connection for tasks | `redis://localhost:6379` |

### Feature Toggles

Set these in your `.env` file:

```env
# Enable/disable features
ENABLE_AI_ANALYTICS=true
ENABLE_CLOUD_BACKUP=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_QUICKBOOKS_SYNC=false
```

## 📊 Monitoring and Health Checks

### Health Endpoints

- **API Health**: `GET /health`
- **Database Health**: `GET /health/db`
- **Redis Health**: `GET /health/redis`

### Monitoring Stack

The Docker deployment includes:

1. **Prometheus** - Metrics collection
2. **Grafana** - Dashboards and visualization
3. **Redis** - Caching and task queue
4. **PostgreSQL** - Production database

### Log Locations

```bash
# Application logs
docker-compose logs inventory-api

# Database logs
docker-compose logs postgres

# Nginx access logs
docker-compose logs nginx
```

## 🔒 Security Checklist

### Production Security Steps

- [ ] Change default passwords
- [ ] Set strong `SECRET_KEY`
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Configure monitoring alerts
- [ ] Review user permissions

### SSL Setup (Production)

1. **Get SSL Certificate** (Let's Encrypt recommended):

```bash
certbot --nginx -d yourdomain.com
```

2. **Update nginx.conf** to enable HTTPS block

3. **Restart services**:

```bash
docker-compose restart nginx
```

## 🧪 Testing and Validation

### Run System Validation

```bash
# Validate entire setup
python validate_setup.py

# Run backend tests
cd backend
pytest test_enhanced_system.py -v

# Test API endpoints
curl http://localhost:8001/health
```

### Performance Testing

```bash
# Load test the API
pip install locust
locust -f backend/load_test.py --host=http://localhost:8001
```

## 🔄 Backup and Recovery

### Automated Backups

The system includes automated backup features:

1. **Database Backups** - Daily PostgreSQL dumps
2. **Cloud Sync** - AWS S3 integration
3. **Configuration Backup** - Environment and settings

### Manual Backup

```bash
# Create database backup
docker-compose exec postgres pg_dump -U inventory_user inventory_db > backup.sql

# Backup application data
docker-compose exec inventory-api python -c "
from cloud_integrations import CloudBackupManager
manager = CloudBackupManager()
manager.create_backup()
"
```

### Recovery

```bash
# Restore database
docker-compose exec -T postgres psql -U inventory_user inventory_db < backup.sql

# Restore from cloud backup
docker-compose exec inventory-api python -c "
from cloud_integrations import CloudBackupManager
manager = CloudBackupManager()
manager.restore_backup('backup-id')
"
```

## 📱 Mobile App Deployment

### Android Build

```bash
cd electronics-mobile-app
npx expo build:android
```

### iOS Build

```bash
cd electronics-mobile-app
npx expo build:ios
```

### App Store Deployment

1. Configure `app.json` with your app details
2. Build signed APK/IPA
3. Upload to Google Play/App Store

## 🖥️ Desktop App Distribution

### Build Executables

```bash
cd desktop/electron-inventory-app
npm run build
```

This creates platform-specific installers in the `dist/` folder.

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Database connection**: Check DATABASE_URL format
3. **Email not sending**: Verify SMTP credentials
4. **Import errors**: Run `pip install -r requirements_core.txt`

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start with verbose output
python start_enhanced_server.py
```

### Reset System

```bash
# Reset database
rm backend/enhanced_inventory.db
python backend/start_enhanced_server.py

# Reset Docker volumes
docker-compose down -v
docker-compose up -d
```

## 📞 Support

### Getting Help

1. **Check logs** first for error messages
2. **Run validation** script to identify issues
3. **Review configuration** files
4. **Check network connectivity** for external services

### Performance Optimization

1. **Database indexing** - Automatic with SQLAlchemy
2. **Redis caching** - Enabled for frequent queries
3. **Background tasks** - Celery for heavy operations
4. **Load balancing** - Nginx configuration included

---

## ✅ Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`requirements_core.txt`)
- [ ] Environment variables configured (`.env`)
- [ ] Database initialized
- [ ] Default users created
- [ ] API accessible on port 8001
- [ ] Desktop app working (optional)
- [ ] Mobile app building (optional)
- [ ] Docker services running (production)
- [ ] SSL configured (production)
- [ ] Backups enabled
- [ ] Monitoring active

**🎉 Your Electronics Store Inventory System is now ready for use!**
