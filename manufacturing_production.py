"""
Manufacturing & Production Management Module
Handles production planning, work orders, quality control, and manufacturing analytics
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enum import Enum
from enhanced_main import Base

logger = logging.getLogger(__name__)

class ProductionStatus(str, Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    QUALITY_CHECK = "quality_check"
    FAILED = "failed"

class WorkOrderType(str, Enum):
    PRODUCTION = "production"
    ASSEMBLY = "assembly"
    TESTING = "testing"
    PACKAGING = "packaging"
    REWORK = "rework"
    MAINTENANCE = "maintenance"

class QualityStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REWORK_REQUIRED = "rework_required"

class MachineStatus(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    BREAKDOWN = "breakdown"
    IDLE = "idle"

# Database Models
class ManufacturingFacility(Base):
    __tablename__ = "manufacturing_facilities"
    
    facility_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    location = Column(String(500))
    capacity_per_day = Column(Integer)
    operating_hours = Column(String(100))  # JSON: start_time, end_time
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class ProductionLine(Base):
    __tablename__ = "production_lines"
    
    line_id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("manufacturing_facilities.facility_id"))
    name = Column(String(200))
    line_type = Column(String(100))  # assembly, testing, packaging
    capacity_per_hour = Column(Integer)
    efficiency_rating = Column(Float, default=100.0)  # Percentage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    facility = relationship("ManufacturingFacility")

class Machine(Base):
    __tablename__ = "machines"
    
    machine_id = Column(Integer, primary_key=True, index=True)
    line_id = Column(Integer, ForeignKey("production_lines.line_id"))
    name = Column(String(200))
    model = Column(String(100))
    serial_number = Column(String(100))
    status = Column(SQLEnum(MachineStatus), default=MachineStatus.OPERATIONAL)
    
    # Performance metrics
    uptime_percentage = Column(Float, default=100.0)
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    
    # Specifications
    specifications = Column(Text)  # JSON
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    production_line = relationship("ProductionLine")

class BillOfMaterials(Base):
    __tablename__ = "bill_of_materials"
    
    bom_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Production details
    production_time_minutes = Column(Integer)
    labor_cost_per_unit = Column(Float)
    overhead_cost_per_unit = Column(Float)
    
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    product = relationship("Product")
    components = relationship("BOMComponent", back_populates="bom")

class BOMComponent(Base):
    __tablename__ = "bom_components"
    
    component_id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bill_of_materials.bom_id"))
    material_product_id = Column(Integer, ForeignKey("products.product_id"))
    
    quantity_required = Column(Float)
    unit_cost = Column(Float)
    is_critical = Column(Boolean, default=False)
    
    # Alternative components
    alternative_products = Column(Text, nullable=True)  # JSON list of product IDs
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    bom = relationship("BillOfMaterials", back_populates="components")
    material = relationship("Product", foreign_keys=[material_product_id])

class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    work_order_id = Column(Integer, primary_key=True, index=True)
    work_order_number = Column(String(100), unique=True, index=True)
    
    # Product and quantity
    product_id = Column(Integer, ForeignKey("products.product_id"))
    bom_id = Column(Integer, ForeignKey("bill_of_materials.bom_id"))
    quantity_ordered = Column(Integer)
    quantity_completed = Column(Integer, default=0)
    quantity_rejected = Column(Integer, default=0)
    
    # Assignment
    facility_id = Column(Integer, ForeignKey("manufacturing_facilities.facility_id"))
    line_id = Column(Integer, ForeignKey("production_lines.line_id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # Status and timing
    status = Column(SQLEnum(ProductionStatus), default=ProductionStatus.PLANNED)
    work_order_type = Column(SQLEnum(WorkOrderType), default=WorkOrderType.PRODUCTION)
    priority = Column(Integer, default=5)  # 1-10, 10 being highest
    
    # Dates
    created_at = Column(DateTime, server_default=func.now())
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # Costs
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Notes and instructions
    instructions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    product = relationship("Product")
    bom = relationship("BillOfMaterials")
    facility = relationship("ManufacturingFacility")
    production_line = relationship("ProductionLine")
    quality_checks = relationship("QualityCheck", back_populates="work_order")

class ProductionRun(Base):
    __tablename__ = "production_runs"
    
    run_id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.work_order_id"))
    run_number = Column(String(100))
    
    # Batch details
    batch_size = Column(Integer)
    units_produced = Column(Integer, default=0)
    units_passed = Column(Integer, default=0)
    units_failed = Column(Integer, default=0)
    
    # Timing
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    
    # Performance metrics
    efficiency_percentage = Column(Float, nullable=True)
    yield_percentage = Column(Float, nullable=True)
    
    # Operator and machine
    operator_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    work_order = relationship("WorkOrder")
    operator = relationship("User")
    machine = relationship("Machine")

class QualityCheck(Base):
    __tablename__ = "quality_checks"
    
    check_id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.work_order_id"))
    run_id = Column(Integer, ForeignKey("production_runs.run_id"), nullable=True)
    
    # Check details
    check_type = Column(String(100))  # incoming, in-process, final
    inspector_id = Column(Integer, ForeignKey("users.user_id"))
    
    # Results
    status = Column(SQLEnum(QualityStatus), default=QualityStatus.PENDING)
    units_checked = Column(Integer)
    units_passed = Column(Integer, default=0)
    units_failed = Column(Integer, default=0)
    
    # Defect tracking
    defect_types = Column(Text, nullable=True)  # JSON
    defect_notes = Column(Text, nullable=True)
    
    # Timing
    check_date = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    work_order = relationship("WorkOrder", back_populates="quality_checks")
    inspector = relationship("User")

# Pydantic Models
class BOMCreate(BaseModel):
    product_id: int
    version: str = "1.0"
    production_time_minutes: int
    labor_cost_per_unit: float
    overhead_cost_per_unit: float
    components: List[Dict[str, Any]]

class WorkOrderCreate(BaseModel):
    product_id: int
    bom_id: int
    quantity_ordered: int
    facility_id: int
    line_id: Optional[int] = None
    priority: int = 5
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    instructions: Optional[str] = None

class ProductionRunCreate(BaseModel):
    work_order_id: int
    batch_size: int
    operator_id: Optional[int] = None
    machine_id: Optional[int] = None

class QualityCheckCreate(BaseModel):
    work_order_id: int
    run_id: Optional[int] = None
    check_type: str
    units_checked: int

class ManufacturingProductionManager:
    """Manufacturing and Production Management System"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_bom(self, bom_data: BOMCreate, user_id: int) -> Dict[str, Any]:
        """Create Bill of Materials"""
        try:
            # Create BOM
            bom = BillOfMaterials(
                product_id=bom_data.product_id,
                version=bom_data.version,
                production_time_minutes=bom_data.production_time_minutes,
                labor_cost_per_unit=bom_data.labor_cost_per_unit,
                overhead_cost_per_unit=bom_data.overhead_cost_per_unit,
                created_by=user_id
            )
            
            self.db.add(bom)
            self.db.commit()
            self.db.refresh(bom)
            
            # Add components
            total_material_cost = 0
            for component_data in bom_data.components:
                component = BOMComponent(
                    bom_id=bom.bom_id,
                    material_product_id=component_data['material_product_id'],
                    quantity_required=component_data['quantity_required'],
                    unit_cost=component_data['unit_cost'],
                    is_critical=component_data.get('is_critical', False)
                )
                
                self.db.add(component)
                total_material_cost += component_data['quantity_required'] * component_data['unit_cost']
            
            self.db.commit()
            
            # Calculate total cost
            total_cost = (
                total_material_cost + 
                bom_data.labor_cost_per_unit + 
                bom_data.overhead_cost_per_unit
            )
            
            return {
                "success": True,
                "bom_id": bom.bom_id,
                "total_material_cost": total_material_cost,
                "total_cost_per_unit": total_cost,
                "components_count": len(bom_data.components)
            }
            
        except Exception as e:
            logger.error(f"BOM creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_work_order(self, work_order_data: WorkOrderCreate, user_id: int) -> Dict[str, Any]:
        """Create work order"""
        try:
            # Generate work order number
            wo_number = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get BOM for cost estimation
            bom = self.db.query(BillOfMaterials).filter(
                BillOfMaterials.bom_id == work_order_data.bom_id
            ).first()
            
            if not bom:
                return {"success": False, "error": "Bill of Materials not found"}
            
            # Calculate estimated cost
            estimated_cost = (
                (bom.labor_cost_per_unit + bom.overhead_cost_per_unit) * 
                work_order_data.quantity_ordered
            )
            
            # Add material costs
            material_cost_query = """
            SELECT SUM(bc.quantity_required * bc.unit_cost * :quantity) as total_material_cost
            FROM bom_components bc
            WHERE bc.bom_id = :bom_id
            """
            
            result = self.db.execute(text(material_cost_query), {
                'bom_id': work_order_data.bom_id,
                'quantity': work_order_data.quantity_ordered
            })
            material_cost = result.fetchone()[0] or 0
            estimated_cost += material_cost
            
            # Create work order
            work_order = WorkOrder(
                work_order_number=wo_number,
                product_id=work_order_data.product_id,
                bom_id=work_order_data.bom_id,
                quantity_ordered=work_order_data.quantity_ordered,
                facility_id=work_order_data.facility_id,
                line_id=work_order_data.line_id,
                priority=work_order_data.priority,
                scheduled_start=work_order_data.scheduled_start,
                scheduled_end=work_order_data.scheduled_end,
                instructions=work_order_data.instructions,
                estimated_cost=estimated_cost,
                created_by=user_id
            )
            
            self.db.add(work_order)
            self.db.commit()
            self.db.refresh(work_order)
            
            return {
                "success": True,
                "work_order_id": work_order.work_order_id,
                "work_order_number": wo_number,
                "estimated_cost": estimated_cost,
                "estimated_duration_hours": bom.production_time_minutes * work_order_data.quantity_ordered / 60
            }
            
        except Exception as e:
            logger.error(f"Work order creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def start_production_run(self, run_data: ProductionRunCreate) -> Dict[str, Any]:
        """Start a production run"""
        try:
            # Get work order
            work_order = self.db.query(WorkOrder).filter(
                WorkOrder.work_order_id == run_data.work_order_id
            ).first()
            
            if not work_order:
                return {"success": False, "error": "Work order not found"}
            
            # Generate run number
            run_number = f"RUN{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create production run
            production_run = ProductionRun(
                work_order_id=run_data.work_order_id,
                run_number=run_number,
                batch_size=run_data.batch_size,
                start_time=datetime.now(),
                operator_id=run_data.operator_id,
                machine_id=run_data.machine_id
            )
            
            self.db.add(production_run)
            
            # Update work order status
            if work_order.status == ProductionStatus.PLANNED:
                work_order.status = ProductionStatus.IN_PROGRESS
                work_order.actual_start = datetime.now()
            
            self.db.commit()
            self.db.refresh(production_run)
            
            return {
                "success": True,
                "run_id": production_run.run_id,
                "run_number": run_number,
                "start_time": production_run.start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Production run start failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def complete_production_run(self, run_id: int, units_produced: int, 
                                    units_passed: int, units_failed: int) -> Dict[str, Any]:
        """Complete a production run"""
        try:
            # Get production run
            production_run = self.db.query(ProductionRun).filter(
                ProductionRun.run_id == run_id
            ).first()
            
            if not production_run:
                return {"success": False, "error": "Production run not found"}
            
            # Update production run
            production_run.end_time = datetime.now()
            production_run.units_produced = units_produced
            production_run.units_passed = units_passed
            production_run.units_failed = units_failed
            
            # Calculate metrics
            if units_produced > 0:
                production_run.yield_percentage = (units_passed / units_produced) * 100
            
            # Calculate efficiency (actual vs planned time)
            if production_run.start_time:
                actual_duration = (production_run.end_time - production_run.start_time).total_seconds() / 3600
                # Get planned duration from BOM
                work_order = self.db.query(WorkOrder).filter(
                    WorkOrder.work_order_id == production_run.work_order_id
                ).first()
                
                if work_order and work_order.bom:
                    planned_duration = (work_order.bom.production_time_minutes * units_produced) / 60
                    if planned_duration > 0:
                        production_run.efficiency_percentage = (planned_duration / actual_duration) * 100
            
            # Update work order quantities
            work_order = production_run.work_order
            work_order.quantity_completed += units_passed
            work_order.quantity_rejected += units_failed
            
            # Check if work order is complete
            if work_order.quantity_completed >= work_order.quantity_ordered:
                work_order.status = ProductionStatus.COMPLETED
                work_order.actual_end = datetime.now()
            
            self.db.commit()
            
            return {
                "success": True,
                "run_id": run_id,
                "yield_percentage": production_run.yield_percentage,
                "efficiency_percentage": production_run.efficiency_percentage,
                "work_order_status": work_order.status
            }
            
        except Exception as e:
            logger.error(f"Production run completion failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_quality_check(self, check_data: QualityCheckCreate, inspector_id: int) -> Dict[str, Any]:
        """Create quality check"""
        try:
            quality_check = QualityCheck(
                work_order_id=check_data.work_order_id,
                run_id=check_data.run_id,
                check_type=check_data.check_type,
                inspector_id=inspector_id,
                units_checked=check_data.units_checked
            )
            
            self.db.add(quality_check)
            self.db.commit()
            self.db.refresh(quality_check)
            
            return {
                "success": True,
                "check_id": quality_check.check_id,
                "status": quality_check.status
            }
            
        except Exception as e:
            logger.error(f"Quality check creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_production_schedule(self, facility_id: Optional[int] = None, 
                                   days_ahead: int = 7) -> Dict[str, Any]:
        """Get production schedule"""
        try:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            query = self.db.query(WorkOrder).filter(
                WorkOrder.scheduled_start.isnot(None),
                WorkOrder.scheduled_start <= end_date,
                WorkOrder.status.in_([ProductionStatus.PLANNED, ProductionStatus.SCHEDULED, ProductionStatus.IN_PROGRESS])
            )
            
            if facility_id:
                query = query.filter(WorkOrder.facility_id == facility_id)
            
            work_orders = query.order_by(WorkOrder.scheduled_start).all()
            
            schedule = []
            for wo in work_orders:
                schedule.append({
                    "work_order_id": wo.work_order_id,
                    "work_order_number": wo.work_order_number,
                    "product_name": wo.product.name if wo.product else "Unknown",
                    "quantity_ordered": wo.quantity_ordered,
                    "quantity_completed": wo.quantity_completed,
                    "status": wo.status,
                    "priority": wo.priority,
                    "scheduled_start": wo.scheduled_start.isoformat() if wo.scheduled_start else None,
                    "scheduled_end": wo.scheduled_end.isoformat() if wo.scheduled_end else None,
                    "facility_name": wo.facility.name if wo.facility else "Unknown"
                })
            
            return {
                "success": True,
                "schedule": schedule,
                "period_days": days_ahead,
                "total_work_orders": len(schedule)
            }
            
        except Exception as e:
            logger.error(f"Production schedule retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_manufacturing_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get manufacturing analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Production summary
            summary_query = """
            SELECT 
                COUNT(*) as total_work_orders,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_orders,
                SUM(quantity_ordered) as total_units_ordered,
                SUM(quantity_completed) as total_units_completed,
                AVG(actual_cost) as avg_production_cost
            FROM work_orders
            WHERE created_at >= :start_date
            """
            
            result = self.db.execute(text(summary_query), {'start_date': start_date})
            summary = dict(result.fetchone())
            
            # Quality metrics
            quality_query = """
            SELECT 
                COUNT(*) as total_checks,
                SUM(units_checked) as total_units_checked,
                SUM(units_passed) as total_units_passed,
                SUM(units_failed) as total_units_failed
            FROM quality_checks
            WHERE check_date >= :start_date
            """
            
            quality_result = self.db.execute(text(quality_query), {'start_date': start_date})
            quality_stats = dict(quality_result.fetchone())
            
            # Calculate metrics
            completion_rate = 0
            if summary['total_work_orders'] > 0:
                completion_rate = (summary['completed_orders'] / summary['total_work_orders']) * 100
            
            quality_rate = 0
            if quality_stats['total_units_checked'] > 0:
                quality_rate = (quality_stats['total_units_passed'] / quality_stats['total_units_checked']) * 100
            
            efficiency_rate = 0
            if summary['total_units_ordered'] > 0:
                efficiency_rate = (summary['total_units_completed'] / summary['total_units_ordered']) * 100
            
            return {
                "success": True,
                "period_days": days_back,
                "production_summary": {
                    "total_work_orders": summary['total_work_orders'] or 0,
                    "completed_orders": summary['completed_orders'] or 0,
                    "active_orders": summary['active_orders'] or 0,
                    "completion_rate": round(completion_rate, 2),
                    "total_units_ordered": summary['total_units_ordered'] or 0,
                    "total_units_completed": summary['total_units_completed'] or 0,
                    "efficiency_rate": round(efficiency_rate, 2),
                    "avg_production_cost": float(summary['avg_production_cost'] or 0)
                },
                "quality_summary": {
                    "total_checks": quality_stats['total_checks'] or 0,
                    "total_units_checked": quality_stats['total_units_checked'] or 0,
                    "total_units_passed": quality_stats['total_units_passed'] or 0,
                    "total_units_failed": quality_stats['total_units_failed'] or 0,
                    "quality_rate": round(quality_rate, 2)
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Manufacturing analytics failed: {e}")
            return {"success": False, "error": str(e)}

def create_manufacturing_manager(db: Session) -> ManufacturingProductionManager:
    """Factory function to create manufacturing manager"""
    return ManufacturingProductionManager(db)
