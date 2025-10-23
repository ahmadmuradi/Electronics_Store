"""
Advanced ERP Integrations Module
Handles integrations with major ERP systems like SAP, Oracle, Microsoft Dynamics, NetSuite
"""

import os
import logging
import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enum import Enum
from enhanced_main import Base
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class ERPSystem(str, Enum):
    SAP = "sap"
    ORACLE_EBS = "oracle_ebs"
    ORACLE_CLOUD = "oracle_cloud"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    NETSUITE = "netsuite"
    SAGE = "sage"
    EPICOR = "epicor"
    INFOR = "infor"

class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class DataEntity(str, Enum):
    CUSTOMERS = "customers"
    SUPPLIERS = "suppliers"
    PRODUCTS = "products"
    INVENTORY = "inventory"
    SALES_ORDERS = "sales_orders"
    PURCHASE_ORDERS = "purchase_orders"
    INVOICES = "invoices"
    PAYMENTS = "payments"
    ACCOUNTS = "accounts"
    COST_CENTERS = "cost_centers"

# Database Models
class ERPConnection(Base):
    __tablename__ = "erp_connections"
    
    connection_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    erp_system = Column(SQLEnum(ERPSystem))
    
    # Connection details
    server_url = Column(String(500))
    database_name = Column(String(100), nullable=True)
    username = Column(String(100))
    password_hash = Column(String(500))  # Encrypted
    api_key = Column(String(500), nullable=True)
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(500), nullable=True)
    
    # Configuration
    sync_frequency_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime, nullable=True)
    
    # Mapping configuration
    field_mappings = Column(Text)  # JSON
    entity_mappings = Column(Text)  # JSON
    
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"))

class ERPSyncLog(Base):
    __tablename__ = "erp_sync_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("erp_connections.connection_id"))
    entity_type = Column(SQLEnum(DataEntity))
    
    # Sync details
    sync_direction = Column(String(20))  # inbound, outbound, bidirectional
    status = Column(SQLEnum(SyncStatus))
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)
    
    # Relationships
    connection = relationship("ERPConnection")

class ERPDataMapping(Base):
    __tablename__ = "erp_data_mappings"
    
    mapping_id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("erp_connections.connection_id"))
    entity_type = Column(SQLEnum(DataEntity))
    
    # Field mapping
    local_field = Column(String(100))
    erp_field = Column(String(100))
    data_type = Column(String(50))
    is_required = Column(Boolean, default=False)
    default_value = Column(String(500), nullable=True)
    
    # Transformation rules
    transformation_rule = Column(Text, nullable=True)  # JSON
    validation_rule = Column(Text, nullable=True)  # JSON
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    connection = relationship("ERPConnection")

# Pydantic Models
class ERPConnectionCreate(BaseModel):
    name: str
    erp_system: ERPSystem
    server_url: str
    database_name: Optional[str] = None
    username: str
    password: str
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    sync_frequency_minutes: int = 60

class SyncRequest(BaseModel):
    connection_id: int
    entity_types: List[DataEntity]
    sync_direction: str = "bidirectional"
    force_full_sync: bool = False

# ERP System Integrations
class SAPIntegration:
    """SAP ERP integration using REST APIs and RFC calls"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.base_url = connection_config.get('server_url')
        self.username = connection_config.get('username')
        self.password = connection_config.get('password')
        self.client = connection_config.get('client_id', '100')
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with SAP system"""
        try:
            # SAP authentication (simplified)
            auth_url = f"{self.base_url}/sap/bc/rest/oauth2/token"
            
            auth_data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password,
                'client_id': self.client
            }
            
            # Simulate authentication
            return {
                "success": True,
                "access_token": "sap_token_123",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"SAP authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_customers(self) -> Dict[str, Any]:
        """Sync customers from SAP"""
        try:
            # SAP Business Partner API
            customers_url = f"{self.base_url}/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner"
            
            # Simulate customer data retrieval
            customers = [
                {
                    "BusinessPartner": "0000100001",
                    "BusinessPartnerName": "ABC Electronics Ltd",
                    "BusinessPartnerCategory": "2",
                    "CreationDate": "2024-01-15T00:00:00"
                },
                {
                    "BusinessPartner": "0000100002", 
                    "BusinessPartnerName": "XYZ Components Inc",
                    "BusinessPartnerCategory": "2",
                    "CreationDate": "2024-01-20T00:00:00"
                }
            ]
            
            return {
                "success": True,
                "customers": customers,
                "count": len(customers)
            }
            
        except Exception as e:
            logger.error(f"SAP customer sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_products(self) -> Dict[str, Any]:
        """Sync products from SAP"""
        try:
            # SAP Material Master API
            products_url = f"{self.base_url}/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product"
            
            # Simulate product data
            products = [
                {
                    "Product": "MAT-001",
                    "ProductDescription": "Smartphone Model X",
                    "ProductType": "FERT",
                    "BaseUnit": "PC",
                    "NetWeight": "0.180",
                    "WeightUnit": "KG"
                }
            ]
            
            return {
                "success": True,
                "products": products,
                "count": len(products)
            }
            
        except Exception as e:
            logger.error(f"SAP product sync failed: {e}")
            return {"success": False, "error": str(e)}

class OracleERPIntegration:
    """Oracle ERP Cloud integration"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.base_url = connection_config.get('server_url')
        self.username = connection_config.get('username')
        self.password = connection_config.get('password')
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Oracle ERP Cloud"""
        try:
            # Oracle Cloud authentication
            return {
                "success": True,
                "access_token": "oracle_token_456",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"Oracle authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_inventory(self) -> Dict[str, Any]:
        """Sync inventory from Oracle ERP"""
        try:
            # Oracle Inventory API
            inventory_url = f"{self.base_url}/fscmRestApi/resources/11.13.18.05/itemsV2"
            
            # Simulate inventory data
            inventory = [
                {
                    "ItemNumber": "ITEM-001",
                    "ItemDescription": "Electronic Component A",
                    "OnHandQuantity": 150,
                    "AvailableQuantity": 120,
                    "UnitOfMeasure": "EA"
                }
            ]
            
            return {
                "success": True,
                "inventory": inventory,
                "count": len(inventory)
            }
            
        except Exception as e:
            logger.error(f"Oracle inventory sync failed: {e}")
            return {"success": False, "error": str(e)}

class MicrosoftDynamicsIntegration:
    """Microsoft Dynamics 365 integration"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.base_url = connection_config.get('server_url')
        self.client_id = connection_config.get('client_id')
        self.client_secret = connection_config.get('client_secret')
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Microsoft Dynamics 365"""
        try:
            # Microsoft OAuth2 authentication
            return {
                "success": True,
                "access_token": "dynamics_token_789",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"Dynamics authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_sales_orders(self) -> Dict[str, Any]:
        """Sync sales orders from Dynamics 365"""
        try:
            # Dynamics Sales Order API
            orders_url = f"{self.base_url}/api/data/v9.2/salesorders"
            
            # Simulate sales order data
            orders = [
                {
                    "salesorderid": "12345678-1234-1234-1234-123456789012",
                    "name": "SO-2024-001",
                    "totalamount": 1500.00,
                    "statecode": 0,
                    "createdon": "2024-01-15T10:30:00Z"
                }
            ]
            
            return {
                "success": True,
                "sales_orders": orders,
                "count": len(orders)
            }
            
        except Exception as e:
            logger.error(f"Dynamics sales order sync failed: {e}")
            return {"success": False, "error": str(e)}

class NetSuiteIntegration:
    """NetSuite ERP integration"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.base_url = connection_config.get('server_url')
        self.api_key = connection_config.get('api_key')
        self.client_id = connection_config.get('client_id')
    
    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with NetSuite"""
        try:
            # NetSuite token-based authentication
            return {
                "success": True,
                "access_token": "netsuite_token_abc",
                "expires_in": 3600
            }
            
        except Exception as e:
            logger.error(f"NetSuite authentication failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_financial_data(self) -> Dict[str, Any]:
        """Sync financial data from NetSuite"""
        try:
            # NetSuite Financial API
            financial_url = f"{self.base_url}/services/NetSuitePort_2021_2.asmx"
            
            # Simulate financial data
            financial_data = [
                {
                    "account_id": "1001",
                    "account_name": "Cash - Operating",
                    "account_type": "Bank",
                    "balance": 50000.00
                }
            ]
            
            return {
                "success": True,
                "financial_data": financial_data,
                "count": len(financial_data)
            }
            
        except Exception as e:
            logger.error(f"NetSuite financial sync failed: {e}")
            return {"success": False, "error": str(e)}

class ERPIntegrationsManager:
    """Main ERP integrations manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.integrations = {
            ERPSystem.SAP: SAPIntegration,
            ERPSystem.ORACLE_EBS: OracleERPIntegration,
            ERPSystem.ORACLE_CLOUD: OracleERPIntegration,
            ERPSystem.MICROSOFT_DYNAMICS: MicrosoftDynamicsIntegration,
            ERPSystem.NETSUITE: NetSuiteIntegration
        }
    
    async def create_erp_connection(self, connection_data: ERPConnectionCreate, user_id: int) -> Dict[str, Any]:
        """Create ERP connection"""
        try:
            # Hash password (in production, use proper encryption)
            password_hash = f"hashed_{connection_data.password}"
            
            connection = ERPConnection(
                name=connection_data.name,
                erp_system=connection_data.erp_system,
                server_url=connection_data.server_url,
                database_name=connection_data.database_name,
                username=connection_data.username,
                password_hash=password_hash,
                api_key=connection_data.api_key,
                client_id=connection_data.client_id,
                client_secret=connection_data.client_secret,
                sync_frequency_minutes=connection_data.sync_frequency_minutes,
                created_by=user_id
            )
            
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            
            # Test connection
            test_result = await self.test_connection(connection.connection_id)
            
            return {
                "success": True,
                "connection_id": connection.connection_id,
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"ERP connection creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def test_connection(self, connection_id: int) -> Dict[str, Any]:
        """Test ERP connection"""
        try:
            connection = self.db.query(ERPConnection).filter(
                ERPConnection.connection_id == connection_id
            ).first()
            
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            # Get integration class
            integration_class = self.integrations.get(connection.erp_system)
            if not integration_class:
                return {"success": False, "error": "ERP system not supported"}
            
            # Create integration instance
            config = {
                'server_url': connection.server_url,
                'username': connection.username,
                'password': 'decrypted_password',  # In production, decrypt
                'api_key': connection.api_key,
                'client_id': connection.client_id,
                'client_secret': connection.client_secret
            }
            
            integration = integration_class(config)
            
            # Test authentication
            auth_result = await integration.authenticate()
            
            return {
                "success": auth_result["success"],
                "message": "Connection test successful" if auth_result["success"] else "Connection test failed",
                "details": auth_result
            }
            
        except Exception as e:
            logger.error(f"ERP connection test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_data(self, sync_request: SyncRequest) -> Dict[str, Any]:
        """Sync data with ERP system"""
        try:
            connection = self.db.query(ERPConnection).filter(
                ERPConnection.connection_id == sync_request.connection_id
            ).first()
            
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            # Create sync log
            sync_log = ERPSyncLog(
                connection_id=sync_request.connection_id,
                entity_type=sync_request.entity_types[0],  # For simplicity, sync first entity
                sync_direction=sync_request.sync_direction,
                status=SyncStatus.IN_PROGRESS
            )
            
            self.db.add(sync_log)
            self.db.commit()
            self.db.refresh(sync_log)
            
            try:
                # Get integration
                integration_class = self.integrations.get(connection.erp_system)
                config = {
                    'server_url': connection.server_url,
                    'username': connection.username,
                    'password': 'decrypted_password',
                    'api_key': connection.api_key,
                    'client_id': connection.client_id,
                    'client_secret': connection.client_secret
                }
                
                integration = integration_class(config)
                
                # Authenticate
                auth_result = await integration.authenticate()
                if not auth_result["success"]:
                    raise Exception(f"Authentication failed: {auth_result['error']}")
                
                # Sync each entity type
                sync_results = []
                total_processed = 0
                total_created = 0
                total_updated = 0
                
                for entity_type in sync_request.entity_types:
                    entity_result = await self._sync_entity(integration, entity_type, connection)
                    sync_results.append(entity_result)
                    
                    if entity_result["success"]:
                        total_processed += entity_result.get("processed", 0)
                        total_created += entity_result.get("created", 0)
                        total_updated += entity_result.get("updated", 0)
                
                # Update sync log
                sync_log.status = SyncStatus.COMPLETED
                sync_log.completed_at = datetime.now()
                sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
                sync_log.records_processed = total_processed
                sync_log.records_created = total_created
                sync_log.records_updated = total_updated
                
                # Update connection last sync
                connection.last_sync = datetime.now()
                
                self.db.commit()
                
                return {
                    "success": True,
                    "sync_log_id": sync_log.log_id,
                    "total_processed": total_processed,
                    "total_created": total_created,
                    "total_updated": total_updated,
                    "duration_seconds": sync_log.duration_seconds,
                    "entity_results": sync_results
                }
                
            except Exception as e:
                # Update sync log with error
                sync_log.status = SyncStatus.FAILED
                sync_log.completed_at = datetime.now()
                sync_log.error_message = str(e)
                self.db.commit()
                
                return {"success": False, "error": str(e), "sync_log_id": sync_log.log_id}
            
        except Exception as e:
            logger.error(f"ERP data sync failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _sync_entity(self, integration, entity_type: DataEntity, connection: ERPConnection) -> Dict[str, Any]:
        """Sync specific entity type"""
        try:
            if entity_type == DataEntity.CUSTOMERS:
                if hasattr(integration, 'sync_customers'):
                    result = await integration.sync_customers()
                    if result["success"]:
                        # Process and store customers
                        return {"success": True, "processed": result["count"], "created": result["count"], "updated": 0}
            
            elif entity_type == DataEntity.PRODUCTS:
                if hasattr(integration, 'sync_products'):
                    result = await integration.sync_products()
                    if result["success"]:
                        return {"success": True, "processed": result["count"], "created": result["count"], "updated": 0}
            
            elif entity_type == DataEntity.INVENTORY:
                if hasattr(integration, 'sync_inventory'):
                    result = await integration.sync_inventory()
                    if result["success"]:
                        return {"success": True, "processed": result["count"], "created": 0, "updated": result["count"]}
            
            elif entity_type == DataEntity.SALES_ORDERS:
                if hasattr(integration, 'sync_sales_orders'):
                    result = await integration.sync_sales_orders()
                    if result["success"]:
                        return {"success": True, "processed": result["count"], "created": result["count"], "updated": 0}
            
            return {"success": False, "error": f"Entity type {entity_type} not supported"}
            
        except Exception as e:
            logger.error(f"Entity sync failed for {entity_type}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_sync_history(self, connection_id: Optional[int] = None, days_back: int = 30) -> Dict[str, Any]:
        """Get ERP sync history"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            query = self.db.query(ERPSyncLog).filter(
                ERPSyncLog.started_at >= start_date
            )
            
            if connection_id:
                query = query.filter(ERPSyncLog.connection_id == connection_id)
            
            sync_logs = query.order_by(ERPSyncLog.started_at.desc()).all()
            
            history = []
            for log in sync_logs:
                history.append({
                    "log_id": log.log_id,
                    "connection_name": log.connection.name if log.connection else "Unknown",
                    "erp_system": log.connection.erp_system if log.connection else "Unknown",
                    "entity_type": log.entity_type,
                    "sync_direction": log.sync_direction,
                    "status": log.status,
                    "records_processed": log.records_processed,
                    "records_created": log.records_created,
                    "records_updated": log.records_updated,
                    "records_failed": log.records_failed,
                    "started_at": log.started_at.isoformat(),
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    "duration_seconds": log.duration_seconds,
                    "error_message": log.error_message
                })
            
            return {
                "success": True,
                "history": history,
                "total_syncs": len(history),
                "period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Sync history retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_erp_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get ERP integration analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Sync summary
            summary_query = """
            SELECT 
                COUNT(*) as total_syncs,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_syncs,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_syncs,
                SUM(records_processed) as total_records_processed,
                AVG(duration_seconds) as avg_duration_seconds
            FROM erp_sync_logs
            WHERE started_at >= :start_date
            """
            
            result = self.db.execute(text(summary_query), {'start_date': start_date})
            summary = dict(result.fetchone())
            
            # ERP system breakdown
            system_query = """
            SELECT 
                ec.erp_system,
                COUNT(esl.log_id) as sync_count,
                COUNT(CASE WHEN esl.status = 'completed' THEN 1 END) as successful_count,
                SUM(esl.records_processed) as total_records
            FROM erp_sync_logs esl
            JOIN erp_connections ec ON esl.connection_id = ec.connection_id
            WHERE esl.started_at >= :start_date
            GROUP BY ec.erp_system
            ORDER BY sync_count DESC
            """
            
            system_result = self.db.execute(text(system_query), {'start_date': start_date})
            system_breakdown = [dict(row) for row in system_result.fetchall()]
            
            # Calculate success rate
            success_rate = 0
            if summary['total_syncs'] > 0:
                success_rate = (summary['successful_syncs'] / summary['total_syncs']) * 100
            
            return {
                "success": True,
                "period_days": days_back,
                "summary": {
                    "total_syncs": summary['total_syncs'] or 0,
                    "successful_syncs": summary['successful_syncs'] or 0,
                    "failed_syncs": summary['failed_syncs'] or 0,
                    "success_rate": round(success_rate, 2),
                    "total_records_processed": summary['total_records_processed'] or 0,
                    "avg_duration_seconds": float(summary['avg_duration_seconds'] or 0)
                },
                "system_breakdown": system_breakdown,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"ERP analytics failed: {e}")
            return {"success": False, "error": str(e)}

def create_erp_manager(db: Session) -> ERPIntegrationsManager:
    """Factory function to create ERP manager"""
    return ERPIntegrationsManager(db)
