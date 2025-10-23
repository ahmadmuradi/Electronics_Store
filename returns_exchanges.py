"""
Returns and Exchanges Management System
Handles product returns, exchanges, refunds, and warranty claims
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enhanced_main import Base

logger = logging.getLogger(__name__)

class ReturnStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ReturnReason(str, Enum):
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    DAMAGED_SHIPPING = "damaged_shipping"
    WARRANTY_CLAIM = "warranty_claim"
    EXCHANGE = "exchange"

class RefundMethod(str, Enum):
    ORIGINAL_PAYMENT = "original_payment"
    STORE_CREDIT = "store_credit"
    CASH = "cash"
    EXCHANGE = "exchange"

# Database Models
class Return(Base):
    __tablename__ = "returns"
    
    return_id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    batch_serial_id = Column(Integer, ForeignKey("batch_serials.id"), nullable=True)
    
    quantity = Column(Integer, default=1)
    reason = Column(SQLEnum(ReturnReason))
    status = Column(SQLEnum(ReturnStatus), default=ReturnStatus.PENDING)
    
    original_price = Column(Float)
    refund_amount = Column(Float, nullable=True)
    refund_method = Column(SQLEnum(RefundMethod), nullable=True)
    
    customer_notes = Column(Text, nullable=True)
    staff_notes = Column(Text, nullable=True)
    
    return_date = Column(DateTime, server_default=func.now())
    approved_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    approved_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    processed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    sale = relationship("Sale", back_populates="returns")
    customer = relationship("Customer")
    product = relationship("Product")
    batch_serial = relationship("BatchSerial")
    approver = relationship("User", foreign_keys=[approved_by])
    processor = relationship("User", foreign_keys=[processed_by])

class Exchange(Base):
    __tablename__ = "exchanges"
    
    exchange_id = Column(Integer, primary_key=True, index=True)
    exchange_number = Column(String(50), unique=True, index=True)
    return_id = Column(Integer, ForeignKey("returns.return_id"))
    
    original_product_id = Column(Integer, ForeignKey("products.product_id"))
    new_product_id = Column(Integer, ForeignKey("products.product_id"))
    
    original_quantity = Column(Integer)
    new_quantity = Column(Integer)
    
    price_difference = Column(Float, default=0.0)  # Positive if customer pays more
    
    status = Column(SQLEnum(ReturnStatus), default=ReturnStatus.PENDING)
    exchange_date = Column(DateTime, server_default=func.now())
    completed_date = Column(DateTime, nullable=True)
    
    processed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    return_request = relationship("Return")
    original_product = relationship("Product", foreign_keys=[original_product_id])
    new_product = relationship("Product", foreign_keys=[new_product_id])
    processor = relationship("User")

class WarrantyClaim(Base):
    __tablename__ = "warranty_claims"
    
    claim_id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(50), unique=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    batch_serial_id = Column(Integer, ForeignKey("batch_serials.id"))
    
    purchase_date = Column(DateTime)
    claim_date = Column(DateTime, server_default=func.now())
    
    issue_description = Column(Text)
    resolution = Column(Text, nullable=True)
    
    status = Column(SQLEnum(ReturnStatus), default=ReturnStatus.PENDING)
    warranty_valid = Column(Boolean, nullable=True)
    
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    assigned_to = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    completed_date = Column(DateTime, nullable=True)
    
    # Relationships
    product = relationship("Product")
    customer = relationship("Customer")
    batch_serial = relationship("BatchSerial")
    technician = relationship("User")

# Pydantic Models
class ReturnCreate(BaseModel):
    sale_id: int
    product_id: int
    quantity: int = 1
    reason: ReturnReason
    customer_notes: Optional[str] = None
    batch_serial_id: Optional[int] = None

class ReturnUpdate(BaseModel):
    status: Optional[ReturnStatus] = None
    refund_amount: Optional[float] = None
    refund_method: Optional[RefundMethod] = None
    staff_notes: Optional[str] = None

class ExchangeCreate(BaseModel):
    return_id: int
    new_product_id: int
    new_quantity: int = 1
    notes: Optional[str] = None

class WarrantyClaimCreate(BaseModel):
    product_id: int
    customer_id: int
    batch_serial_id: int
    purchase_date: datetime
    issue_description: str

class ReturnsExchangesManager:
    """Main manager for returns and exchanges"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_return(self, return_data: ReturnCreate, customer_id: int) -> Dict[str, Any]:
        """Create a new return request"""
        try:
            # Validate sale and product
            sale_query = """
            SELECT s.*, si.price, si.quantity as sold_quantity
            FROM sales s
            JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.sale_id = :sale_id AND si.product_id = :product_id
            """
            
            result = self.db.execute(text(sale_query), {
                'sale_id': return_data.sale_id,
                'product_id': return_data.product_id
            })
            sale_item = result.fetchone()
            
            if not sale_item:
                return {"success": False, "error": "Sale item not found"}
            
            if return_data.quantity > sale_item.sold_quantity:
                return {"success": False, "error": "Return quantity exceeds sold quantity"}
            
            # Check return policy (e.g., 30 days)
            return_deadline = sale_item.sale_date + timedelta(days=30)
            if datetime.now() > return_deadline:
                return {"success": False, "error": "Return period has expired"}
            
            # Generate return number
            return_number = f"RET{datetime.now().strftime('%Y%m%d')}{self._get_next_return_sequence():04d}"
            
            # Create return record
            new_return = Return(
                return_number=return_number,
                sale_id=return_data.sale_id,
                customer_id=customer_id,
                product_id=return_data.product_id,
                batch_serial_id=return_data.batch_serial_id,
                quantity=return_data.quantity,
                reason=return_data.reason,
                original_price=sale_item.price,
                customer_notes=return_data.customer_notes
            )
            
            self.db.add(new_return)
            self.db.commit()
            self.db.refresh(new_return)
            
            # Log the return request
            await self._log_return_activity(new_return.return_id, "Return request created")
            
            return {
                "success": True,
                "return_id": new_return.return_id,
                "return_number": return_number,
                "status": new_return.status
            }
            
        except Exception as e:
            logger.error(f"Return creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def process_return(self, return_id: int, update_data: ReturnUpdate, user_id: int) -> Dict[str, Any]:
        """Process a return request (approve/reject/complete)"""
        try:
            # Get return record
            return_record = self.db.query(Return).filter(Return.return_id == return_id).first()
            if not return_record:
                return {"success": False, "error": "Return not found"}
            
            old_status = return_record.status
            
            # Update return record
            if update_data.status:
                return_record.status = update_data.status
                
                if update_data.status == ReturnStatus.APPROVED:
                    return_record.approved_date = datetime.now()
                    return_record.approved_by = user_id
                elif update_data.status == ReturnStatus.COMPLETED:
                    return_record.completed_date = datetime.now()
                    return_record.processed_by = user_id
            
            if update_data.refund_amount is not None:
                return_record.refund_amount = update_data.refund_amount
            
            if update_data.refund_method:
                return_record.refund_method = update_data.refund_method
            
            if update_data.staff_notes:
                return_record.staff_notes = update_data.staff_notes
            
            # Handle inventory restoration for completed returns
            if (update_data.status == ReturnStatus.COMPLETED and 
                old_status != ReturnStatus.COMPLETED):
                await self._restore_inventory(return_record)
            
            self.db.commit()
            
            # Log the status change
            await self._log_return_activity(
                return_id, 
                f"Status changed from {old_status} to {update_data.status}"
            )
            
            return {
                "success": True,
                "return_id": return_id,
                "new_status": return_record.status,
                "refund_amount": return_record.refund_amount
            }
            
        except Exception as e:
            logger.error(f"Return processing failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_exchange(self, exchange_data: ExchangeCreate, user_id: int) -> Dict[str, Any]:
        """Create a product exchange"""
        try:
            # Get return record
            return_record = self.db.query(Return).filter(Return.return_id == exchange_data.return_id).first()
            if not return_record:
                return {"success": False, "error": "Return not found"}
            
            if return_record.status != ReturnStatus.APPROVED:
                return {"success": False, "error": "Return must be approved before exchange"}
            
            # Get product prices
            original_product_query = "SELECT price FROM products WHERE product_id = :product_id"
            new_product_query = "SELECT price, stock_quantity FROM products WHERE product_id = :product_id"
            
            original_result = self.db.execute(text(original_product_query), 
                                            {'product_id': return_record.product_id})
            original_product = original_result.fetchone()
            
            new_result = self.db.execute(text(new_product_query), 
                                       {'product_id': exchange_data.new_product_id})
            new_product = new_result.fetchone()
            
            if not new_product:
                return {"success": False, "error": "New product not found"}
            
            if new_product.stock_quantity < exchange_data.new_quantity:
                return {"success": False, "error": "Insufficient stock for exchange"}
            
            # Calculate price difference
            price_difference = (new_product.price * exchange_data.new_quantity) - \
                             (original_product.price * return_record.quantity)
            
            # Generate exchange number
            exchange_number = f"EXC{datetime.now().strftime('%Y%m%d')}{self._get_next_exchange_sequence():04d}"
            
            # Create exchange record
            new_exchange = Exchange(
                exchange_number=exchange_number,
                return_id=exchange_data.return_id,
                original_product_id=return_record.product_id,
                new_product_id=exchange_data.new_product_id,
                original_quantity=return_record.quantity,
                new_quantity=exchange_data.new_quantity,
                price_difference=price_difference,
                processed_by=user_id,
                notes=exchange_data.notes
            )
            
            self.db.add(new_exchange)
            
            # Update return status
            return_record.status = ReturnStatus.PROCESSING
            
            # Adjust inventory
            await self._process_exchange_inventory(new_exchange)
            
            self.db.commit()
            self.db.refresh(new_exchange)
            
            return {
                "success": True,
                "exchange_id": new_exchange.exchange_id,
                "exchange_number": exchange_number,
                "price_difference": price_difference
            }
            
        except Exception as e:
            logger.error(f"Exchange creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def create_warranty_claim(self, claim_data: WarrantyClaimCreate) -> Dict[str, Any]:
        """Create a warranty claim"""
        try:
            # Validate warranty period
            warranty_period = await self._get_warranty_period(claim_data.product_id)
            warranty_expiry = claim_data.purchase_date + timedelta(days=warranty_period)
            
            if datetime.now() > warranty_expiry:
                warranty_valid = False
            else:
                warranty_valid = True
            
            # Generate claim number
            claim_number = f"WAR{datetime.now().strftime('%Y%m%d')}{self._get_next_warranty_sequence():04d}"
            
            # Create warranty claim
            new_claim = WarrantyClaim(
                claim_number=claim_number,
                product_id=claim_data.product_id,
                customer_id=claim_data.customer_id,
                batch_serial_id=claim_data.batch_serial_id,
                purchase_date=claim_data.purchase_date,
                issue_description=claim_data.issue_description,
                warranty_valid=warranty_valid
            )
            
            self.db.add(new_claim)
            self.db.commit()
            self.db.refresh(new_claim)
            
            return {
                "success": True,
                "claim_id": new_claim.claim_id,
                "claim_number": claim_number,
                "warranty_valid": warranty_valid,
                "warranty_expiry": warranty_expiry.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Warranty claim creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_returns_report(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate returns and exchanges report"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Returns summary
            returns_query = """
            SELECT 
                r.status,
                r.reason,
                COUNT(*) as count,
                SUM(r.refund_amount) as total_refund,
                AVG(r.refund_amount) as avg_refund
            FROM returns r
            WHERE r.return_date >= :start_date
            GROUP BY r.status, r.reason
            ORDER BY count DESC
            """
            
            returns_result = self.db.execute(text(returns_query), {'start_date': start_date})
            returns_summary = [dict(row) for row in returns_result.fetchall()]
            
            # Top returned products
            top_returns_query = """
            SELECT 
                p.name,
                p.sku,
                COUNT(*) as return_count,
                SUM(r.quantity) as total_quantity
            FROM returns r
            JOIN products p ON r.product_id = p.product_id
            WHERE r.return_date >= :start_date
            GROUP BY p.product_id, p.name, p.sku
            ORDER BY return_count DESC
            LIMIT 10
            """
            
            top_returns_result = self.db.execute(text(top_returns_query), {'start_date': start_date})
            top_returned_products = [dict(row) for row in top_returns_result.fetchall()]
            
            # Financial impact
            financial_query = """
            SELECT 
                COUNT(*) as total_returns,
                SUM(r.refund_amount) as total_refunds,
                AVG(r.refund_amount) as avg_refund,
                SUM(CASE WHEN r.status = 'completed' THEN r.refund_amount ELSE 0 END) as completed_refunds
            FROM returns r
            WHERE r.return_date >= :start_date
            """
            
            financial_result = self.db.execute(text(financial_query), {'start_date': start_date})
            financial_impact = dict(financial_result.fetchone())
            
            return {
                "success": True,
                "period_days": days_back,
                "returns_summary": returns_summary,
                "top_returned_products": top_returned_products,
                "financial_impact": financial_impact,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Returns report generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    def _get_next_return_sequence(self) -> int:
        """Get next return sequence number for today"""
        today = datetime.now().strftime('%Y%m%d')
        query = "SELECT COUNT(*) FROM returns WHERE return_number LIKE :pattern"
        result = self.db.execute(text(query), {'pattern': f'RET{today}%'})
        return result.scalar() + 1
    
    def _get_next_exchange_sequence(self) -> int:
        """Get next exchange sequence number for today"""
        today = datetime.now().strftime('%Y%m%d')
        query = "SELECT COUNT(*) FROM exchanges WHERE exchange_number LIKE :pattern"
        result = self.db.execute(text(query), {'pattern': f'EXC{today}%'})
        return result.scalar() + 1
    
    def _get_next_warranty_sequence(self) -> int:
        """Get next warranty claim sequence number for today"""
        today = datetime.now().strftime('%Y%m%d')
        query = "SELECT COUNT(*) FROM warranty_claims WHERE claim_number LIKE :pattern"
        result = self.db.execute(text(query), {'pattern': f'WAR{today}%'})
        return result.scalar() + 1
    
    async def _restore_inventory(self, return_record: Return):
        """Restore inventory for completed return"""
        try:
            # Update main product stock
            update_query = """
            UPDATE products 
            SET stock_quantity = stock_quantity + :quantity
            WHERE product_id = :product_id
            """
            
            self.db.execute(text(update_query), {
                'quantity': return_record.quantity,
                'product_id': return_record.product_id
            })
            
            # Update batch/serial status if applicable
            if return_record.batch_serial_id:
                batch_update_query = """
                UPDATE batch_serials 
                SET status = 'returned'
                WHERE id = :batch_serial_id
                """
                
                self.db.execute(text(batch_update_query), {
                    'batch_serial_id': return_record.batch_serial_id
                })
            
        except Exception as e:
            logger.error(f"Inventory restoration failed: {e}")
            raise
    
    async def _process_exchange_inventory(self, exchange: Exchange):
        """Process inventory changes for exchange"""
        try:
            # Reduce stock for new product
            reduce_query = """
            UPDATE products 
            SET stock_quantity = stock_quantity - :quantity
            WHERE product_id = :product_id
            """
            
            self.db.execute(text(reduce_query), {
                'quantity': exchange.new_quantity,
                'product_id': exchange.new_product_id
            })
            
        except Exception as e:
            logger.error(f"Exchange inventory processing failed: {e}")
            raise
    
    async def _get_warranty_period(self, product_id: int) -> int:
        """Get warranty period in days for a product"""
        query = "SELECT warranty_days FROM products WHERE product_id = :product_id"
        result = self.db.execute(text(query), {'product_id': product_id})
        warranty_row = result.fetchone()
        return warranty_row.warranty_days if warranty_row and warranty_row.warranty_days else 365
    
    async def _log_return_activity(self, return_id: int, activity: str):
        """Log return activity for audit trail"""
        try:
            log_query = """
            INSERT INTO audit_logs (table_name, record_id, action, details, created_at)
            VALUES ('returns', :return_id, 'update', :activity, CURRENT_TIMESTAMP)
            """
            
            self.db.execute(text(log_query), {
                'return_id': return_id,
                'activity': activity
            })
            
        except Exception as e:
            logger.error(f"Return activity logging failed: {e}")


def create_returns_manager(db: Session) -> ReturnsExchangesManager:
    """Factory function to create returns manager"""
    return ReturnsExchangesManager(db)
