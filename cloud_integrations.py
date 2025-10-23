"""
Cloud Backup and Integration Module
Supports cloud backup, QuickBooks/Xero integration, and email notifications
"""

import os
import json
import boto3
import asyncio
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import requests
from requests_oauthlib import OAuth2Session
import pandas as pd
from io import StringIO, BytesIO

logger = logging.getLogger(__name__)

class CloudBackupManager:
    """Manages automated cloud backups"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        self.backup_bucket = os.environ.get('BACKUP_BUCKET_NAME', 'electronics-store-backups')
        
        # Initialize S3 client if credentials are available
        if self.aws_access_key and self.aws_secret_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
        else:
            self.s3_client = None
            logger.warning("AWS credentials not configured - cloud backup disabled")
    
    async def create_database_backup(self) -> Dict:
        """Create a complete database backup"""
        try:
            backup_data = {}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Define tables to backup
            tables = [
                'users', 'locations', 'suppliers', 'categories', 'products',
                'product_locations', 'batch_serials', 'customers', 'sales',
                'sale_items', 'inventory_transactions', 'purchase_orders',
                'purchase_order_items', 'reorder_alerts', 'audit_logs'
            ]
            
            # Export each table
            for table in tables:
                try:
                    query = f"SELECT * FROM {table}"
                    result = self.db.execute(text(query))
                    
                    # Convert to list of dictionaries
                    columns = result.keys()
                    rows = []
                    for row in result.fetchall():
                        row_dict = {}
                        for i, col in enumerate(columns):
                            value = row[i]
                            # Handle datetime objects
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            row_dict[col] = value
                        rows.append(row_dict)
                    
                    backup_data[table] = {
                        'columns': list(columns),
                        'data': rows,
                        'count': len(rows)
                    }
                    
                    logger.info(f"Backed up {len(rows)} records from {table}")
                    
                except Exception as e:
                    logger.error(f"Error backing up table {table}: {str(e)}")
                    backup_data[table] = {'error': str(e)}
            
            # Add metadata
            backup_data['_metadata'] = {
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'total_tables': len(tables)
            }
            
            # Save locally first
            local_filename = f"backup_{timestamp}.json"
            local_path = f"backups/{local_filename}"
            os.makedirs("backups", exist_ok=True)
            
            async with aiofiles.open(local_path, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2))
            
            # Upload to cloud if configured
            cloud_url = None
            if self.s3_client:
                try:
                    cloud_key = f"database_backups/{local_filename}"
                    self.s3_client.upload_file(local_path, self.backup_bucket, cloud_key)
                    cloud_url = f"s3://{self.backup_bucket}/{cloud_key}"
                    logger.info(f"Backup uploaded to cloud: {cloud_url}")
                except Exception as e:
                    logger.error(f"Failed to upload backup to cloud: {str(e)}")
            
            return {
                "success": True,
                "timestamp": timestamp,
                "local_path": local_path,
                "cloud_url": cloud_url,
                "tables_backed_up": len([t for t in backup_data.keys() if not t.startswith('_') and 'error' not in backup_data[t]]),
                "total_records": sum([backup_data[t].get('count', 0) for t in backup_data.keys() if not t.startswith('_') and 'count' in backup_data[t]])
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def restore_from_backup(self, backup_path: str) -> Dict:
        """Restore database from backup file"""
        try:
            # Load backup data
            if backup_path.startswith('s3://'):
                # Download from S3
                bucket, key = backup_path.replace('s3://', '').split('/', 1)
                local_path = f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.s3_client.download_file(bucket, key, local_path)
                backup_path = local_path
            
            async with aiofiles.open(backup_path, 'r') as f:
                backup_data = json.loads(await f.read())
            
            restored_tables = 0
            restored_records = 0
            
            # Restore each table
            for table_name, table_data in backup_data.items():
                if table_name.startswith('_') or 'error' in table_data:
                    continue
                
                try:
                    # Clear existing data (be careful!)
                    self.db.execute(text(f"DELETE FROM {table_name}"))
                    
                    # Insert backup data
                    if table_data['data']:
                        columns = table_data['columns']
                        placeholders = ', '.join([f':{col}' for col in columns])
                        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        for row in table_data['data']:
                            self.db.execute(text(query), row)
                        
                        restored_tables += 1
                        restored_records += len(table_data['data'])
                        logger.info(f"Restored {len(table_data['data'])} records to {table_name}")
                
                except Exception as e:
                    logger.error(f"Error restoring table {table_name}: {str(e)}")
            
            self.db.commit()
            
            # Clean up temp file if downloaded from S3
            if backup_path.startswith('temp_restore_'):
                os.remove(backup_path)
            
            return {
                "success": True,
                "restored_tables": restored_tables,
                "restored_records": restored_records,
                "backup_timestamp": backup_data.get('_metadata', {}).get('timestamp', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        # List local backups
        if os.path.exists("backups"):
            for filename in os.listdir("backups"):
                if filename.endswith('.json'):
                    filepath = f"backups/{filename}"
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "location": "local"
                    })
        
        # List cloud backups
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.backup_bucket,
                    Prefix="database_backups/"
                )
                
                for obj in response.get('Contents', []):
                    backups.append({
                        "filename": obj['Key'].split('/')[-1],
                        "path": f"s3://{self.backup_bucket}/{obj['Key']}",
                        "size": obj['Size'],
                        "created": obj['LastModified'].isoformat(),
                        "location": "cloud"
                    })
            except Exception as e:
                logger.error(f"Error listing cloud backups: {str(e)}")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

class QuickBooksIntegration:
    """Integration with QuickBooks Online API"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.client_id = os.environ.get('QUICKBOOKS_CLIENT_ID')
        self.client_secret = os.environ.get('QUICKBOOKS_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('QUICKBOOKS_REDIRECT_URI', 'http://localhost:8001/auth/quickbooks/callback')
        self.sandbox_base_url = "https://sandbox-quickbooks.api.intuit.com"
        self.discovery_document_url = "https://appcenter.intuit.com/api/v1/OpenID_OIDC_Discovery_Document"
        
        # OAuth2 session
        self.oauth = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['com.intuit.quickbooks.accounting']
        )
    
    def get_authorization_url(self) -> str:
        """Get QuickBooks authorization URL"""
        authorization_url, state = self.oauth.authorization_url(
            'https://appcenter.intuit.com/connect/oauth2'
        )
        return authorization_url
    
    async def exchange_code_for_tokens(self, authorization_code: str, company_id: str) -> Dict:
        """Exchange authorization code for access tokens"""
        try:
            token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
            
            token = self.oauth.fetch_token(
                token_url,
                authorization_response=authorization_code,
                client_secret=self.client_secret
            )
            
            # Store tokens securely (in production, encrypt these)
            # For now, we'll return them
            return {
                "success": True,
                "access_token": token['access_token'],
                "refresh_token": token['refresh_token'],
                "company_id": company_id,
                "expires_at": token.get('expires_at')
            }
            
        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_customers_to_quickbooks(self, access_token: str, company_id: str) -> Dict:
        """Sync customers from inventory system to QuickBooks"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Get customers from database
            customers = self.db.execute(text("SELECT * FROM customers")).fetchall()
            
            synced_count = 0
            errors = []
            
            for customer in customers:
                try:
                    # Create customer in QuickBooks
                    customer_data = {
                        "Name": f"{customer.first_name} {customer.last_name}".strip(),
                        "CompanyName": f"Customer {customer.customer_id}",
                        "BillAddr": {
                            "Line1": customer.address or "",
                        },
                        "PrimaryPhone": {
                            "FreeFormNumber": customer.phone or ""
                        },
                        "PrimaryEmailAddr": {
                            "Address": customer.email or ""
                        }
                    }
                    
                    url = f"{self.sandbox_base_url}/v3/company/{company_id}/customer"
                    response = requests.post(url, headers=headers, json=customer_data)
                    
                    if response.status_code == 200:
                        synced_count += 1
                    else:
                        errors.append(f"Customer {customer.customer_id}: {response.text}")
                        
                except Exception as e:
                    errors.append(f"Customer {customer.customer_id}: {str(e)}")
            
            return {
                "success": True,
                "synced_customers": synced_count,
                "total_customers": len(customers),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Customer sync failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def sync_sales_to_quickbooks(self, access_token: str, company_id: str, 
                                     start_date: Optional[datetime] = None) -> Dict:
        """Sync sales from inventory system to QuickBooks as invoices"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Get sales from database
            query = """
            SELECT s.*, c.first_name, c.last_name, c.email
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.customer_id
            """
            
            if start_date:
                query += f" WHERE s.sale_date >= '{start_date.isoformat()}'"
            
            sales = self.db.execute(text(query)).fetchall()
            
            synced_count = 0
            errors = []
            
            for sale in sales:
                try:
                    # Get sale items
                    items_query = """
                    SELECT si.*, p.name, p.price
                    FROM sale_items si
                    JOIN products p ON si.product_id = p.product_id
                    WHERE si.sale_id = :sale_id
                    """
                    
                    items = self.db.execute(text(items_query), {'sale_id': sale.sale_id}).fetchall()
                    
                    # Create invoice in QuickBooks
                    line_items = []
                    for item in items:
                        line_items.append({
                            "Amount": float(item.price * item.quantity),
                            "DetailType": "SalesItemLineDetail",
                            "SalesItemLineDetail": {
                                "ItemRef": {
                                    "value": "1",  # Default item - in production, map to actual QB items
                                    "name": item.name
                                },
                                "Qty": item.quantity,
                                "UnitPrice": float(item.price)
                            }
                        })
                    
                    invoice_data = {
                        "Line": line_items,
                        "CustomerRef": {
                            "value": "1"  # Default customer - in production, map to actual QB customers
                        },
                        "TotalAmt": float(sale.total_amount),
                        "TxnDate": sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    url = f"{self.sandbox_base_url}/v3/company/{company_id}/invoice"
                    response = requests.post(url, headers=headers, json=invoice_data)
                    
                    if response.status_code == 200:
                        synced_count += 1
                    else:
                        errors.append(f"Sale {sale.sale_id}: {response.text}")
                        
                except Exception as e:
                    errors.append(f"Sale {sale.sale_id}: {str(e)}")
            
            return {
                "success": True,
                "synced_sales": synced_count,
                "total_sales": len(sales),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Sales sync failed: {str(e)}")
            return {"success": False, "error": str(e)}

class EmailNotificationSystem:
    """Comprehensive email notification system"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.company_name = os.environ.get('COMPANY_NAME', 'Electronics Store')
    
    async def send_email(self, to_emails: List[str], subject: str, 
                        html_body: str, text_body: Optional[str] = None,
                        attachments: Optional[List[Dict]] = None) -> Dict:
        """Send email with optional attachments"""
        try:
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.company_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            
            # Add text and HTML parts
            if text_body:
                msg.attach(MimeText(text_body, 'plain'))
            msg.attach(MimeText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MimeBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, to_emails, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return {"success": True, "recipients": to_emails}
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_low_stock_alert(self, manager_email: str, low_stock_items: List[Dict]) -> Dict:
        """Send low stock alert email"""
        subject = f"🚨 Low Stock Alert - {self.company_name}"
        
        items_html = ""
        for item in low_stock_items:
            items_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px;">{item['product_name']}</td>
                <td style="padding: 10px; text-align: center;">{item['current_stock']}</td>
                <td style="padding: 10px; text-align: center;">{item['reorder_level']}</td>
                <td style="padding: 10px; text-align: center; color: #dc3545; font-weight: bold;">
                    {item['suggested_quantity']}
                </td>
            </tr>
            """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 Low Stock Alert</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Immediate attention required</p>
                </div>
                
                <div style="padding: 20px;">
                    <p>The following items are running low and need to be reordered:</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background-color: #f8f9fa;">
                                <th style="padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6;">Product</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Current Stock</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Reorder Level</th>
                                <th style="padding: 12px; text-align: center; border-bottom: 2px solid #dee2e6;">Suggested Order</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                        <strong>⚠️ Action Required:</strong> Please review these items and create purchase orders as needed.
                    </div>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        This alert was generated automatically by the {self.company_name} Inventory Management System.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email([manager_email], subject, html_body)
    
    async def send_sales_report(self, recipient_email: str, report_data: Dict, 
                               report_period: str) -> Dict:
        """Send sales report email"""
        subject = f"📊 Sales Report - {report_period} - {self.company_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">📊 Sales Report</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">{report_period}</p>
                </div>
                
                <div style="padding: 20px;">
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                            <h3 style="margin: 0; color: #495057;">Total Sales</h3>
                            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #28a745;">
                                {report_data.get('total_sales', 0)}
                            </p>
                        </div>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                            <h3 style="margin: 0; color: #495057;">Total Revenue</h3>
                            <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: #28a745;">
                                ${report_data.get('total_revenue', 0):,.2f}
                            </p>
                        </div>
                    </div>
                    
                    <h3>Top Selling Products:</h3>
                    <ul style="list-style-type: none; padding: 0;">
                        {self._format_top_products(report_data.get('top_products', []))}
                    </ul>
                    
                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {self.company_name} Inventory System.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email([recipient_email], subject, html_body)
    
    def _format_top_products(self, products: List[Dict]) -> str:
        """Format top products for email"""
        html = ""
        for i, product in enumerate(products[:5], 1):
            html += f"""
            <li style="padding: 10px; margin: 5px 0; background-color: #f8f9fa; border-radius: 5px;">
                <strong>{i}. {product.get('name', 'Unknown')}</strong> - 
                {product.get('quantity_sold', 0)} units sold 
                (${product.get('revenue', 0):,.2f})
            </li>
            """
        return html

# Factory function to create integration instances
def create_integrations(db_session: Session) -> Dict:
    """Create integration instances"""
    return {
        "cloud_backup": CloudBackupManager(db_session),
        "quickbooks": QuickBooksIntegration(db_session),
        "email_notifications": EmailNotificationSystem()
    }
