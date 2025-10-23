"""
Shipping & Logistics Integration Module
Handles integrations with major shipping carriers and logistics providers
"""

import os
import logging
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enum import Enum
from enhanced_main import Base
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ShippingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"
    CANCELLED = "cancelled"

class ShippingCarrier(str, Enum):
    FEDEX = "fedex"
    UPS = "ups"
    DHL = "dhl"
    USPS = "usps"
    ARAMEX = "aramex"
    TNT = "tnt"
    CUSTOM = "custom"

class ShippingService(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"
    SAME_DAY = "same_day"
    INTERNATIONAL = "international"

# Database Models
class ShippingProvider(Base):
    __tablename__ = "shipping_providers"
    
    provider_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    carrier = Column(SQLEnum(ShippingCarrier))
    api_endpoint = Column(String(500))
    api_key = Column(String(200))
    api_secret = Column(String(200))
    account_number = Column(String(50))
    is_active = Column(Boolean, default=True)
    supports_tracking = Column(Boolean, default=True)
    supports_labels = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class ShippingZone(Base):
    __tablename__ = "shipping_zones"
    
    zone_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    countries = Column(Text)  # JSON list of country codes
    states = Column(Text, nullable=True)  # JSON list of state codes
    postal_codes = Column(Text, nullable=True)  # JSON list of postal code patterns
    is_domestic = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class ShippingRate(Base):
    __tablename__ = "shipping_rates"
    
    rate_id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("shipping_providers.provider_id"))
    zone_id = Column(Integer, ForeignKey("shipping_zones.zone_id"))
    service_type = Column(SQLEnum(ShippingService))
    
    # Weight-based pricing
    min_weight = Column(Float, default=0)
    max_weight = Column(Float, default=999999)
    
    # Value-based pricing
    min_value = Column(Float, default=0)
    max_value = Column(Float, default=999999)
    
    # Pricing
    base_rate = Column(Float)
    per_kg_rate = Column(Float, default=0)
    per_item_rate = Column(Float, default=0)
    
    # Delivery time
    min_delivery_days = Column(Integer)
    max_delivery_days = Column(Integer)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    provider = relationship("ShippingProvider")
    zone = relationship("ShippingZone")

class Shipment(Base):
    __tablename__ = "shipments"
    
    shipment_id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String(100), unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id"))
    provider_id = Column(Integer, ForeignKey("shipping_providers.provider_id"))
    
    # Tracking information
    tracking_number = Column(String(100), nullable=True)
    carrier_reference = Column(String(100), nullable=True)
    
    # Status and timing
    status = Column(SQLEnum(ShippingStatus), default=ShippingStatus.PENDING)
    service_type = Column(SQLEnum(ShippingService))
    
    # Addresses
    sender_address = Column(Text)  # JSON
    recipient_address = Column(Text)  # JSON
    
    # Package details
    weight = Column(Float)
    dimensions = Column(Text)  # JSON: length, width, height
    declared_value = Column(Float)
    insurance_value = Column(Float, nullable=True)
    
    # Costs
    shipping_cost = Column(Float)
    insurance_cost = Column(Float, default=0)
    total_cost = Column(Float)
    
    # Dates
    created_at = Column(DateTime, server_default=func.now())
    shipped_at = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Additional data
    label_url = Column(String(500), nullable=True)
    carrier_response = Column(Text, nullable=True)
    
    # Relationships
    sale = relationship("Sale")
    provider = relationship("ShippingProvider")
    tracking_events = relationship("ShipmentTracking", back_populates="shipment")

class ShipmentTracking(Base):
    __tablename__ = "shipment_tracking"
    
    tracking_id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.shipment_id"))
    
    status = Column(String(100))
    description = Column(Text)
    location = Column(String(200), nullable=True)
    timestamp = Column(DateTime)
    
    # Raw carrier data
    carrier_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    shipment = relationship("Shipment", back_populates="tracking_events")

# Pydantic Models
class AddressCreate(BaseModel):
    name: str
    company: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None

class ShipmentCreate(BaseModel):
    sale_id: int
    provider_id: int
    service_type: ShippingService
    sender_address: AddressCreate
    recipient_address: AddressCreate
    weight: float
    length: float
    width: float
    height: float
    declared_value: float
    insurance_value: Optional[float] = None

class ShippingRateRequest(BaseModel):
    sender_address: AddressCreate
    recipient_address: AddressCreate
    weight: float
    length: float
    width: float
    height: float
    declared_value: float

# Shipping Carrier Integrations
class FedExIntegration:
    """FedEx shipping integration"""
    
    def __init__(self, api_key: str, api_secret: str, account_number: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.account_number = account_number
        self.base_url = "https://apis.fedex.com"
        self.test_url = "https://apis-sandbox.fedex.com"
    
    async def get_rates(self, request: ShippingRateRequest) -> Dict[str, Any]:
        """Get shipping rates from FedEx"""
        try:
            # FedEx Rate API call
            payload = {
                "accountNumber": {"value": self.account_number},
                "requestedShipment": {
                    "shipper": {
                        "address": {
                            "postalCode": request.sender_address.postal_code,
                            "countryCode": request.sender_address.country
                        }
                    },
                    "recipient": {
                        "address": {
                            "postalCode": request.recipient_address.postal_code,
                            "countryCode": request.recipient_address.country
                        }
                    },
                    "requestedPackageLineItems": [{
                        "weight": {
                            "units": "KG",
                            "value": request.weight
                        },
                        "dimensions": {
                            "length": request.length,
                            "width": request.width,
                            "height": request.height,
                            "units": "CM"
                        }
                    }]
                }
            }
            
            # Simulate API response (replace with actual FedEx API call)
            rates = [
                {
                    "service_type": "FEDEX_GROUND",
                    "rate": 15.99,
                    "currency": "USD",
                    "delivery_days": "3-5"
                },
                {
                    "service_type": "FEDEX_EXPRESS_SAVER",
                    "rate": 25.99,
                    "currency": "USD",
                    "delivery_days": "1-2"
                }
            ]
            
            return {"success": True, "rates": rates}
            
        except Exception as e:
            logger.error(f"FedEx rate request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_shipment(self, shipment_data: ShipmentCreate) -> Dict[str, Any]:
        """Create FedEx shipment"""
        try:
            # FedEx Ship API call
            payload = {
                "labelResponseOptions": "URL_ONLY",
                "requestedShipment": {
                    "shipper": {
                        "contact": {
                            "personName": shipment_data.sender_address.name,
                            "phoneNumber": shipment_data.sender_address.phone
                        },
                        "address": {
                            "streetLines": [shipment_data.sender_address.address_line1],
                            "city": shipment_data.sender_address.city,
                            "stateOrProvinceCode": shipment_data.sender_address.state,
                            "postalCode": shipment_data.sender_address.postal_code,
                            "countryCode": shipment_data.sender_address.country
                        }
                    },
                    "recipients": [{
                        "contact": {
                            "personName": shipment_data.recipient_address.name,
                            "phoneNumber": shipment_data.recipient_address.phone
                        },
                        "address": {
                            "streetLines": [shipment_data.recipient_address.address_line1],
                            "city": shipment_data.recipient_address.city,
                            "stateOrProvinceCode": shipment_data.recipient_address.state,
                            "postalCode": shipment_data.recipient_address.postal_code,
                            "countryCode": shipment_data.recipient_address.country
                        }
                    }]
                }
            }
            
            # Simulate successful shipment creation
            tracking_number = f"FX{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return {
                "success": True,
                "tracking_number": tracking_number,
                "label_url": f"https://fedex.com/labels/{tracking_number}.pdf",
                "estimated_delivery": (datetime.now() + timedelta(days=3)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"FedEx shipment creation failed: {e}")
            return {"success": False, "error": str(e)}

class UPSIntegration:
    """UPS shipping integration"""
    
    def __init__(self, api_key: str, username: str, password: str):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.base_url = "https://onlinetools.ups.com"
    
    async def get_rates(self, request: ShippingRateRequest) -> Dict[str, Any]:
        """Get shipping rates from UPS"""
        try:
            # UPS Rating API
            rates = [
                {
                    "service_type": "UPS_GROUND",
                    "rate": 12.99,
                    "currency": "USD",
                    "delivery_days": "3-5"
                },
                {
                    "service_type": "UPS_NEXT_DAY_AIR",
                    "rate": 35.99,
                    "currency": "USD",
                    "delivery_days": "1"
                }
            ]
            
            return {"success": True, "rates": rates}
            
        except Exception as e:
            logger.error(f"UPS rate request failed: {e}")
            return {"success": False, "error": str(e)}

class DHLIntegration:
    """DHL shipping integration"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://express.api.dhl.com"
    
    async def get_rates(self, request: ShippingRateRequest) -> Dict[str, Any]:
        """Get shipping rates from DHL"""
        try:
            rates = [
                {
                    "service_type": "DHL_EXPRESS_WORLDWIDE",
                    "rate": 45.99,
                    "currency": "USD",
                    "delivery_days": "1-3"
                }
            ]
            
            return {"success": True, "rates": rates}
            
        except Exception as e:
            logger.error(f"DHL rate request failed: {e}")
            return {"success": False, "error": str(e)}

class ShippingLogisticsManager:
    """Main shipping and logistics manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.carriers = {}
        self.load_carriers()
    
    def load_carriers(self):
        """Load configured shipping carriers"""
        try:
            # Load FedEx
            if os.environ.get('FEDEX_API_KEY'):
                self.carriers['fedex'] = FedExIntegration(
                    os.environ.get('FEDEX_API_KEY'),
                    os.environ.get('FEDEX_API_SECRET'),
                    os.environ.get('FEDEX_ACCOUNT_NUMBER')
                )
            
            # Load UPS
            if os.environ.get('UPS_API_KEY'):
                self.carriers['ups'] = UPSIntegration(
                    os.environ.get('UPS_API_KEY'),
                    os.environ.get('UPS_USERNAME'),
                    os.environ.get('UPS_PASSWORD')
                )
            
            # Load DHL
            if os.environ.get('DHL_API_KEY'):
                self.carriers['dhl'] = DHLIntegration(
                    os.environ.get('DHL_API_KEY'),
                    os.environ.get('DHL_API_SECRET')
                )
            
        except Exception as e:
            logger.error(f"Failed to load carriers: {e}")
    
    async def get_shipping_rates(self, request: ShippingRateRequest) -> Dict[str, Any]:
        """Get shipping rates from all available carriers"""
        try:
            all_rates = []
            
            for carrier_name, carrier in self.carriers.items():
                try:
                    rates_result = await carrier.get_rates(request)
                    if rates_result["success"]:
                        for rate in rates_result["rates"]:
                            rate["carrier"] = carrier_name
                            all_rates.append(rate)
                except Exception as e:
                    logger.error(f"Failed to get rates from {carrier_name}: {e}")
            
            # Sort by price
            all_rates.sort(key=lambda x: x["rate"])
            
            return {
                "success": True,
                "rates": all_rates,
                "count": len(all_rates)
            }
            
        except Exception as e:
            logger.error(f"Shipping rates request failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_shipment(self, shipment_data: ShipmentCreate) -> Dict[str, Any]:
        """Create a new shipment"""
        try:
            # Get provider
            provider = self.db.query(ShippingProvider).filter(
                ShippingProvider.provider_id == shipment_data.provider_id
            ).first()
            
            if not provider:
                return {"success": False, "error": "Shipping provider not found"}
            
            # Generate shipment number
            shipment_number = f"SH{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create shipment record
            shipment = Shipment(
                shipment_number=shipment_number,
                sale_id=shipment_data.sale_id,
                provider_id=shipment_data.provider_id,
                status=ShippingStatus.PENDING,
                service_type=shipment_data.service_type,
                sender_address=json.dumps(shipment_data.sender_address.dict()),
                recipient_address=json.dumps(shipment_data.recipient_address.dict()),
                weight=shipment_data.weight,
                dimensions=json.dumps({
                    "length": shipment_data.length,
                    "width": shipment_data.width,
                    "height": shipment_data.height
                }),
                declared_value=shipment_data.declared_value,
                insurance_value=shipment_data.insurance_value
            )
            
            self.db.add(shipment)
            self.db.commit()
            self.db.refresh(shipment)
            
            # Create shipment with carrier
            carrier_name = provider.carrier.value
            if carrier_name in self.carriers:
                carrier_result = await self.carriers[carrier_name].create_shipment(shipment_data)
                
                if carrier_result["success"]:
                    # Update shipment with carrier data
                    shipment.tracking_number = carrier_result["tracking_number"]
                    shipment.label_url = carrier_result.get("label_url")
                    shipment.estimated_delivery = datetime.fromisoformat(
                        carrier_result["estimated_delivery"].replace('Z', '+00:00')
                    ) if carrier_result.get("estimated_delivery") else None
                    shipment.status = ShippingStatus.PROCESSING
                    shipment.carrier_response = json.dumps(carrier_result)
                    
                    self.db.commit()
            
            return {
                "success": True,
                "shipment_id": shipment.shipment_id,
                "shipment_number": shipment_number,
                "tracking_number": shipment.tracking_number,
                "label_url": shipment.label_url,
                "estimated_delivery": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None
            }
            
        except Exception as e:
            logger.error(f"Shipment creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track shipment status"""
        try:
            # Find shipment
            shipment = self.db.query(Shipment).filter(
                Shipment.tracking_number == tracking_number
            ).first()
            
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            # Get latest tracking events
            tracking_events = self.db.query(ShipmentTracking).filter(
                ShipmentTracking.shipment_id == shipment.shipment_id
            ).order_by(ShipmentTracking.timestamp.desc()).all()
            
            # Simulate real-time tracking (replace with actual carrier API calls)
            if not tracking_events:
                # Create initial tracking event
                initial_event = ShipmentTracking(
                    shipment_id=shipment.shipment_id,
                    status="PICKED_UP",
                    description="Package picked up by carrier",
                    location=json.loads(shipment.sender_address)["city"],
                    timestamp=datetime.now()
                )
                self.db.add(initial_event)
                self.db.commit()
                tracking_events = [initial_event]
            
            return {
                "success": True,
                "shipment_number": shipment.shipment_number,
                "tracking_number": tracking_number,
                "status": shipment.status,
                "estimated_delivery": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
                "tracking_events": [
                    {
                        "status": event.status,
                        "description": event.description,
                        "location": event.location,
                        "timestamp": event.timestamp.isoformat()
                    }
                    for event in tracking_events
                ]
            }
            
        except Exception as e:
            logger.error(f"Shipment tracking failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_shipping_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get shipping and logistics analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Shipment summary
            summary_query = """
            SELECT 
                COUNT(*) as total_shipments,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_count,
                COUNT(CASE WHEN status = 'in_transit' THEN 1 END) as in_transit_count,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                AVG(shipping_cost) as avg_shipping_cost,
                SUM(shipping_cost) as total_shipping_cost
            FROM shipments
            WHERE created_at >= :start_date
            """
            
            result = self.db.execute(text(summary_query), {'start_date': start_date})
            summary = dict(result.fetchone())
            
            # Carrier performance
            carrier_query = """
            SELECT 
                sp.name as carrier_name,
                COUNT(s.shipment_id) as shipment_count,
                AVG(s.shipping_cost) as avg_cost,
                COUNT(CASE WHEN s.status = 'delivered' THEN 1 END) as delivered_count
            FROM shipments s
            JOIN shipping_providers sp ON s.provider_id = sp.provider_id
            WHERE s.created_at >= :start_date
            GROUP BY sp.provider_id, sp.name
            ORDER BY shipment_count DESC
            """
            
            carrier_result = self.db.execute(text(carrier_query), {'start_date': start_date})
            carrier_performance = [dict(row) for row in carrier_result.fetchall()]
            
            # Calculate delivery performance
            delivery_rate = 0
            if summary['total_shipments'] > 0:
                delivery_rate = (summary['delivered_count'] / summary['total_shipments']) * 100
            
            return {
                "success": True,
                "period_days": days_back,
                "summary": {
                    "total_shipments": summary['total_shipments'] or 0,
                    "delivered_count": summary['delivered_count'] or 0,
                    "in_transit_count": summary['in_transit_count'] or 0,
                    "failed_count": summary['failed_count'] or 0,
                    "delivery_rate": round(delivery_rate, 2),
                    "avg_shipping_cost": float(summary['avg_shipping_cost'] or 0),
                    "total_shipping_cost": float(summary['total_shipping_cost'] or 0)
                },
                "carrier_performance": carrier_performance,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Shipping analytics failed: {e}")
            return {"success": False, "error": str(e)}

def create_shipping_manager(db: Session) -> ShippingLogisticsManager:
    """Factory function to create shipping manager"""
    return ShippingLogisticsManager(db)
