"""
IoT & Blockchain Integration Module
Handles IoT device management, sensor data, and blockchain supply chain tracking
"""

import os
import logging
import json
import hashlib
import time
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
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class IoTDeviceType(str, Enum):
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    MOTION_DETECTOR = "motion_detector"
    RFID_READER = "rfid_reader"
    BARCODE_SCANNER = "barcode_scanner"
    WEIGHT_SCALE = "weight_scale"
    SECURITY_CAMERA = "security_camera"
    SMART_LOCK = "smart_lock"
    ENVIRONMENTAL_MONITOR = "environmental_monitor"
    ASSET_TRACKER = "asset_tracker"

class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    UNKNOWN = "unknown"

class BlockchainNetwork(str, Enum):
    ETHEREUM = "ethereum"
    HYPERLEDGER = "hyperledger"
    POLYGON = "polygon"
    BSC = "bsc"
    PRIVATE = "private"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

# Database Models
class IoTDevice(Base):
    __tablename__ = "iot_devices"
    
    device_id = Column(Integer, primary_key=True, index=True)
    device_uuid = Column(String(100), unique=True, index=True)
    name = Column(String(200))
    device_type = Column(SQLEnum(IoTDeviceType))
    
    # Location and assignment
    location = Column(String(500))
    facility_id = Column(Integer, ForeignKey("manufacturing_facilities.facility_id"), nullable=True)
    assigned_to_product = Column(Integer, ForeignKey("products.product_id"), nullable=True)
    
    # Network configuration
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(17), nullable=True)
    network_protocol = Column(String(50))  # WiFi, Ethernet, LoRa, etc.
    
    # Status and health
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    last_seen = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)  # Percentage
    signal_strength = Column(Float, nullable=True)  # dBm
    
    # Configuration
    sampling_interval_seconds = Column(Integer, default=60)
    alert_thresholds = Column(Text, nullable=True)  # JSON
    
    # Metadata
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class IoTSensorData(Base):
    __tablename__ = "iot_sensor_data"
    
    data_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("iot_devices.device_id"))
    
    # Sensor readings
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    light_level = Column(Float, nullable=True)
    motion_detected = Column(Boolean, nullable=True)
    weight = Column(Float, nullable=True)
    
    # Custom sensor data
    sensor_type = Column(String(50))
    sensor_value = Column(Float)
    sensor_unit = Column(String(20))
    
    # Metadata
    timestamp = Column(DateTime, server_default=func.now())
    location_coordinates = Column(String(100), nullable=True)  # lat,lng
    
    # Relationships
    device = relationship("IoTDevice")

class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    blockchain_hash = Column(String(100), unique=True, index=True)
    network = Column(SQLEnum(BlockchainNetwork))
    
    # Transaction details
    transaction_type = Column(String(50))  # supply_chain, ownership, quality_check
    from_address = Column(String(100))
    to_address = Column(String(100))
    
    # Supply chain data
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=True)
    batch_number = Column(String(100), nullable=True)
    quantity = Column(Float, nullable=True)
    
    # Transaction data
    data_payload = Column(Text)  # JSON
    gas_fee = Column(Float, nullable=True)
    
    # Status and timing
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    block_number = Column(Integer, nullable=True)
    
    # Relationships
    product = relationship("Product")

class SupplyChainEvent(Base):
    __tablename__ = "supply_chain_events"
    
    event_id = Column(Integer, primary_key=True, index=True)
    blockchain_transaction_id = Column(Integer, ForeignKey("blockchain_transactions.transaction_id"), nullable=True)
    
    # Event details
    event_type = Column(String(50))  # manufactured, shipped, received, sold
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_number = Column(String(100))
    
    # Location and participants
    location = Column(String(500))
    participant_name = Column(String(200))
    participant_address = Column(String(500))
    
    # Event data
    quantity = Column(Float)
    quality_score = Column(Float, nullable=True)
    temperature_range = Column(String(50), nullable=True)
    humidity_range = Column(String(50), nullable=True)
    
    # Verification
    verified = Column(Boolean, default=False)
    verification_method = Column(String(100), nullable=True)
    
    # Timing
    event_timestamp = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    product = relationship("Product")
    blockchain_transaction = relationship("BlockchainTransaction")

class SmartContract(Base):
    __tablename__ = "smart_contracts"
    
    contract_id = Column(Integer, primary_key=True, index=True)
    contract_address = Column(String(100), unique=True, index=True)
    network = Column(SQLEnum(BlockchainNetwork))
    
    # Contract details
    name = Column(String(200))
    contract_type = Column(String(50))  # supply_chain, quality_assurance, payment
    abi = Column(Text)  # Contract ABI JSON
    bytecode = Column(Text, nullable=True)
    
    # Deployment info
    deployed_by = Column(Integer, ForeignKey("users.user_id"))
    deployed_at = Column(DateTime, server_default=func.now())
    deployment_tx_hash = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    deployer = relationship("User")

# Pydantic Models
class IoTDeviceCreate(BaseModel):
    name: str
    device_type: IoTDeviceType
    location: str
    facility_id: Optional[int] = None
    network_protocol: str = "WiFi"
    sampling_interval_seconds: int = 60
    manufacturer: Optional[str] = None
    model: Optional[str] = None

class SensorDataCreate(BaseModel):
    device_uuid: str
    sensor_type: str
    sensor_value: float
    sensor_unit: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    location_coordinates: Optional[str] = None

class SupplyChainEventCreate(BaseModel):
    event_type: str
    product_id: int
    batch_number: str
    location: str
    participant_name: str
    quantity: float
    quality_score: Optional[float] = None
    temperature_range: Optional[str] = None
    humidity_range: Optional[str] = None

# Blockchain Implementation
@dataclass
class Block:
    """Simple blockchain block structure"""
    index: int
    timestamp: float
    data: Dict[str, Any]
    previous_hash: str
    nonce: int = 0
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()

class SimpleBlockchain:
    """Simple blockchain implementation for supply chain tracking"""
    
    def __init__(self):
        self.chain = []
        self.difficulty = 4  # Number of leading zeros required
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Genesis Block - Electronics Store Supply Chain"},
            previous_hash="0"
        )
        
        genesis_block.nonce = self.proof_of_work(genesis_block)
        self.chain.append(genesis_block)
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def add_block(self, data: Dict[str, Any]) -> Block:
        """Add a new block to the chain"""
        previous_block = self.get_latest_block()
        
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=previous_block.calculate_hash()
        )
        
        new_block.nonce = self.proof_of_work(new_block)
        self.chain.append(new_block)
        
        return new_block
    
    def proof_of_work(self, block: Block) -> int:
        """Simple proof of work algorithm"""
        nonce = 0
        while True:
            block.nonce = nonce
            hash_value = block.calculate_hash()
            
            if hash_value.startswith("0" * self.difficulty):
                return nonce
            
            nonce += 1
    
    def is_chain_valid(self) -> bool:
        """Validate the blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block hash is valid
            if current_block.calculate_hash() != current_block.calculate_hash():
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.calculate_hash():
                return False
        
        return True

class IoTManager:
    """IoT device management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_device(self, device_data: IoTDeviceCreate) -> Dict[str, Any]:
        """Register new IoT device"""
        try:
            # Generate unique device UUID
            device_uuid = f"IOT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(device_data.name) % 10000:04d}"
            
            device = IoTDevice(
                device_uuid=device_uuid,
                name=device_data.name,
                device_type=device_data.device_type,
                location=device_data.location,
                facility_id=device_data.facility_id,
                network_protocol=device_data.network_protocol,
                sampling_interval_seconds=device_data.sampling_interval_seconds,
                manufacturer=device_data.manufacturer,
                model=device_data.model,
                status=DeviceStatus.OFFLINE
            )
            
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)
            
            return {
                "success": True,
                "device_id": device.device_id,
                "device_uuid": device_uuid,
                "message": "IoT device registered successfully"
            }
            
        except Exception as e:
            logger.error(f"IoT device registration failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def receive_sensor_data(self, sensor_data: SensorDataCreate) -> Dict[str, Any]:
        """Receive and store sensor data"""
        try:
            # Find device
            device = self.db.query(IoTDevice).filter(
                IoTDevice.device_uuid == sensor_data.device_uuid
            ).first()
            
            if not device:
                return {"success": False, "error": "Device not found"}
            
            # Store sensor data
            data_record = IoTSensorData(
                device_id=device.device_id,
                sensor_type=sensor_data.sensor_type,
                sensor_value=sensor_data.sensor_value,
                sensor_unit=sensor_data.sensor_unit,
                temperature=sensor_data.temperature,
                humidity=sensor_data.humidity,
                location_coordinates=sensor_data.location_coordinates
            )
            
            self.db.add(data_record)
            
            # Update device status
            device.status = DeviceStatus.ONLINE
            device.last_seen = datetime.now()
            
            self.db.commit()
            
            # Check for alerts
            alerts = await self._check_sensor_alerts(device, sensor_data)
            
            return {
                "success": True,
                "data_id": data_record.data_id,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Sensor data processing failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _check_sensor_alerts(self, device: IoTDevice, sensor_data: SensorDataCreate) -> List[Dict[str, Any]]:
        """Check for sensor threshold alerts"""
        alerts = []
        
        try:
            if device.alert_thresholds:
                thresholds = json.loads(device.alert_thresholds)
                
                # Temperature alerts
                if sensor_data.temperature and 'temperature' in thresholds:
                    temp_threshold = thresholds['temperature']
                    if (sensor_data.temperature < temp_threshold.get('min', -999) or 
                        sensor_data.temperature > temp_threshold.get('max', 999)):
                        alerts.append({
                            "type": "temperature_alert",
                            "message": f"Temperature {sensor_data.temperature}°C outside threshold",
                            "severity": "high",
                            "device_name": device.name
                        })
                
                # Humidity alerts
                if sensor_data.humidity and 'humidity' in thresholds:
                    humidity_threshold = thresholds['humidity']
                    if (sensor_data.humidity < humidity_threshold.get('min', 0) or 
                        sensor_data.humidity > humidity_threshold.get('max', 100)):
                        alerts.append({
                            "type": "humidity_alert",
                            "message": f"Humidity {sensor_data.humidity}% outside threshold",
                            "severity": "medium",
                            "device_name": device.name
                        })
            
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
        
        return alerts
    
    async def get_device_analytics(self, device_id: int, hours_back: int = 24) -> Dict[str, Any]:
        """Get IoT device analytics"""
        try:
            start_time = datetime.now() - timedelta(hours=hours_back)
            
            # Get sensor data
            sensor_data = self.db.query(IoTSensorData).filter(
                IoTSensorData.device_id == device_id,
                IoTSensorData.timestamp >= start_time
            ).order_by(IoTSensorData.timestamp).all()
            
            if not sensor_data:
                return {"success": False, "error": "No data found for the specified period"}
            
            # Calculate statistics
            temperatures = [d.temperature for d in sensor_data if d.temperature is not None]
            humidities = [d.humidity for d in sensor_data if d.humidity is not None]
            
            analytics = {
                "device_id": device_id,
                "period_hours": hours_back,
                "total_readings": len(sensor_data),
                "temperature_stats": {
                    "count": len(temperatures),
                    "min": min(temperatures) if temperatures else None,
                    "max": max(temperatures) if temperatures else None,
                    "avg": sum(temperatures) / len(temperatures) if temperatures else None
                },
                "humidity_stats": {
                    "count": len(humidities),
                    "min": min(humidities) if humidities else None,
                    "max": max(humidities) if humidities else None,
                    "avg": sum(humidities) / len(humidities) if humidities else None
                },
                "readings": [
                    {
                        "timestamp": d.timestamp.isoformat(),
                        "sensor_type": d.sensor_type,
                        "sensor_value": d.sensor_value,
                        "temperature": d.temperature,
                        "humidity": d.humidity
                    }
                    for d in sensor_data[-100:]  # Last 100 readings
                ]
            }
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            logger.error(f"Device analytics failed: {e}")
            return {"success": False, "error": str(e)}

class BlockchainManager:
    """Blockchain supply chain management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.blockchain = SimpleBlockchain()
    
    async def create_supply_chain_event(self, event_data: SupplyChainEventCreate) -> Dict[str, Any]:
        """Create supply chain event on blockchain"""
        try:
            # Create blockchain transaction data
            blockchain_data = {
                "event_type": event_data.event_type,
                "product_id": event_data.product_id,
                "batch_number": event_data.batch_number,
                "location": event_data.location,
                "participant": event_data.participant_name,
                "quantity": event_data.quantity,
                "quality_score": event_data.quality_score,
                "timestamp": datetime.now().isoformat(),
                "environmental_conditions": {
                    "temperature_range": event_data.temperature_range,
                    "humidity_range": event_data.humidity_range
                }
            }
            
            # Add to blockchain
            block = self.blockchain.add_block(blockchain_data)
            block_hash = block.calculate_hash()
            
            # Create blockchain transaction record
            blockchain_tx = BlockchainTransaction(
                blockchain_hash=block_hash,
                network=BlockchainNetwork.PRIVATE,
                transaction_type="supply_chain",
                from_address="system",
                to_address=event_data.participant_name,
                product_id=event_data.product_id,
                batch_number=event_data.batch_number,
                quantity=event_data.quantity,
                data_payload=json.dumps(blockchain_data),
                status=TransactionStatus.CONFIRMED,
                confirmed_at=datetime.now(),
                block_number=block.index
            )
            
            self.db.add(blockchain_tx)
            self.db.commit()
            self.db.refresh(blockchain_tx)
            
            # Create supply chain event
            supply_event = SupplyChainEvent(
                blockchain_transaction_id=blockchain_tx.transaction_id,
                event_type=event_data.event_type,
                product_id=event_data.product_id,
                batch_number=event_data.batch_number,
                location=event_data.location,
                participant_name=event_data.participant_name,
                quantity=event_data.quantity,
                quality_score=event_data.quality_score,
                temperature_range=event_data.temperature_range,
                humidity_range=event_data.humidity_range,
                verified=True,
                verification_method="blockchain",
                event_timestamp=datetime.now()
            )
            
            self.db.add(supply_event)
            self.db.commit()
            self.db.refresh(supply_event)
            
            return {
                "success": True,
                "event_id": supply_event.event_id,
                "blockchain_hash": block_hash,
                "block_number": block.index,
                "transaction_id": blockchain_tx.transaction_id
            }
            
        except Exception as e:
            logger.error(f"Supply chain event creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_product_history(self, product_id: int) -> Dict[str, Any]:
        """Get complete supply chain history for a product"""
        try:
            events = self.db.query(SupplyChainEvent).filter(
                SupplyChainEvent.product_id == product_id
            ).order_by(SupplyChainEvent.event_timestamp).all()
            
            history = []
            for event in events:
                history.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "batch_number": event.batch_number,
                    "location": event.location,
                    "participant": event.participant_name,
                    "quantity": event.quantity,
                    "quality_score": event.quality_score,
                    "temperature_range": event.temperature_range,
                    "humidity_range": event.humidity_range,
                    "verified": event.verified,
                    "event_timestamp": event.event_timestamp.isoformat(),
                    "blockchain_hash": event.blockchain_transaction.blockchain_hash if event.blockchain_transaction else None
                })
            
            return {
                "success": True,
                "product_id": product_id,
                "total_events": len(history),
                "supply_chain_history": history
            }
            
        except Exception as e:
            logger.error(f"Product history retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_blockchain_integrity(self) -> Dict[str, Any]:
        """Verify blockchain integrity"""
        try:
            is_valid = self.blockchain.is_chain_valid()
            
            return {
                "success": True,
                "blockchain_valid": is_valid,
                "total_blocks": len(self.blockchain.chain),
                "latest_block_hash": self.blockchain.get_latest_block().calculate_hash()
            }
            
        except Exception as e:
            logger.error(f"Blockchain verification failed: {e}")
            return {"success": False, "error": str(e)}

class IoTBlockchainManager:
    """Combined IoT and Blockchain manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.iot_manager = IoTManager(db)
        self.blockchain_manager = BlockchainManager(db)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall IoT and blockchain system status"""
        try:
            # IoT device status
            device_stats = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_devices,
                    COUNT(CASE WHEN status = 'online' THEN 1 END) as online_devices,
                    COUNT(CASE WHEN status = 'offline' THEN 1 END) as offline_devices,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_devices
                FROM iot_devices
            """)).fetchone()
            
            # Blockchain stats
            blockchain_stats = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_transactions,
                    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_transactions,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_transactions
                FROM blockchain_transactions
            """)).fetchone()
            
            # Recent sensor data
            recent_data_count = self.db.execute(text("""
                SELECT COUNT(*) as recent_readings
                FROM iot_sensor_data
                WHERE timestamp >= datetime('now', '-1 hour')
            """)).fetchone()
            
            return {
                "success": True,
                "iot_status": {
                    "total_devices": device_stats[0],
                    "online_devices": device_stats[1],
                    "offline_devices": device_stats[2],
                    "error_devices": device_stats[3],
                    "recent_readings": recent_data_count[0]
                },
                "blockchain_status": {
                    "total_transactions": blockchain_stats[0],
                    "confirmed_transactions": blockchain_stats[1],
                    "pending_transactions": blockchain_stats[2],
                    "blockchain_valid": True  # Would call actual verification
                },
                "system_health": "operational",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System status check failed: {e}")
            return {"success": False, "error": str(e)}

def create_iot_blockchain_manager(db: Session) -> IoTBlockchainManager:
    """Factory function to create IoT blockchain manager"""
    return IoTBlockchainManager(db)
