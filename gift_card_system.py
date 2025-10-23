"""
Gift Card System Module
Handles gift card creation, redemption, and management
"""

import os
import logging
import secrets
import string
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

class GiftCardStatus(str, Enum):
    ACTIVE = "active"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PARTIALLY_USED = "partially_used"

class GiftCardType(str, Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    PROMOTIONAL = "promotional"

# Database Models
class GiftCard(Base):
    __tablename__ = "gift_cards"
    
    gift_card_id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String(20), unique=True, index=True)
    pin_code = Column(String(10), nullable=True)  # Optional PIN for security
    
    initial_amount = Column(Float)
    current_balance = Column(Float)
    currency = Column(String(3), default="USD")
    
    card_type = Column(SQLEnum(GiftCardType), default=GiftCardType.DIGITAL)
    status = Column(SQLEnum(GiftCardStatus), default=GiftCardStatus.ACTIVE)
    
    # Recipient information
    recipient_name = Column(String(200), nullable=True)
    recipient_email = Column(String(200), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    
    # Purchaser information
    purchaser_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)
    purchased_by_name = Column(String(200), nullable=True)
    purchased_by_email = Column(String(200), nullable=True)
    
    # Dates
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Message and customization
    personal_message = Column(Text, nullable=True)
    design_template = Column(String(100), nullable=True)
    
    # Relationships
    purchaser = relationship("Customer", foreign_keys=[purchaser_id])
    transactions = relationship("GiftCardTransaction", back_populates="gift_card")

class GiftCardTransaction(Base):
    __tablename__ = "gift_card_transactions"
    
    transaction_id = Column(Integer, primary_key=True, index=True)
    gift_card_id = Column(Integer, ForeignKey("gift_cards.gift_card_id"))
    sale_id = Column(Integer, ForeignKey("sales.sale_id"), nullable=True)
    
    transaction_type = Column(String(20))  # 'purchase', 'redemption', 'refund', 'adjustment'
    amount = Column(Float)
    balance_before = Column(Float)
    balance_after = Column(Float)
    
    description = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    gift_card = relationship("GiftCard", back_populates="transactions")
    sale = relationship("Sale")
    user = relationship("User")

class GiftCardPromotion(Base):
    __tablename__ = "gift_card_promotions"
    
    promotion_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    description = Column(Text)
    
    # Promotion rules
    min_purchase_amount = Column(Float, default=0)
    bonus_percentage = Column(Float, default=0)  # e.g., 10% bonus
    bonus_fixed_amount = Column(Float, default=0)  # e.g., $10 bonus
    
    # Validity
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())

# Pydantic Models
class GiftCardCreate(BaseModel):
    amount: float
    card_type: GiftCardType = GiftCardType.DIGITAL
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    purchaser_name: Optional[str] = None
    purchaser_email: Optional[str] = None
    personal_message: Optional[str] = None
    design_template: Optional[str] = None
    expires_in_days: Optional[int] = 365  # Default 1 year expiry

class GiftCardRedeem(BaseModel):
    card_number: str
    pin_code: Optional[str] = None
    amount: float

class GiftCardBalance(BaseModel):
    card_number: str
    pin_code: Optional[str] = None

class GiftCardManager:
    """Gift Card Management System"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _generate_card_number(self) -> str:
        """Generate unique gift card number"""
        while True:
            # Generate 16-digit card number
            card_number = ''.join(secrets.choice(string.digits) for _ in range(16))
            
            # Check if already exists
            existing = self.db.query(GiftCard).filter(
                GiftCard.card_number == card_number
            ).first()
            
            if not existing:
                return card_number
    
    def _generate_pin_code(self) -> str:
        """Generate 6-digit PIN code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    async def create_gift_card(self, gift_card_data: GiftCardCreate, purchaser_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new gift card"""
        try:
            # Generate card number and PIN
            card_number = self._generate_card_number()
            pin_code = self._generate_pin_code()
            
            # Calculate expiry date
            expires_at = None
            if gift_card_data.expires_in_days:
                expires_at = datetime.now() + timedelta(days=gift_card_data.expires_in_days)
            
            # Create gift card
            gift_card = GiftCard(
                card_number=card_number,
                pin_code=pin_code,
                initial_amount=gift_card_data.amount,
                current_balance=gift_card_data.amount,
                card_type=gift_card_data.card_type,
                recipient_name=gift_card_data.recipient_name,
                recipient_email=gift_card_data.recipient_email,
                recipient_phone=gift_card_data.recipient_phone,
                purchaser_id=purchaser_id,
                purchased_by_name=gift_card_data.purchaser_name,
                purchased_by_email=gift_card_data.purchaser_email,
                personal_message=gift_card_data.personal_message,
                design_template=gift_card_data.design_template,
                expires_at=expires_at,
                activated_at=datetime.now()
            )
            
            self.db.add(gift_card)
            self.db.commit()
            self.db.refresh(gift_card)
            
            # Create initial transaction
            transaction = GiftCardTransaction(
                gift_card_id=gift_card.gift_card_id,
                transaction_type='purchase',
                amount=gift_card_data.amount,
                balance_before=0,
                balance_after=gift_card_data.amount,
                description=f'Gift card created with initial amount ${gift_card_data.amount}'
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            # Send gift card email if recipient email provided
            if gift_card_data.recipient_email:
                await self._send_gift_card_email(gift_card)
            
            return {
                "success": True,
                "gift_card_id": gift_card.gift_card_id,
                "card_number": card_number,
                "pin_code": pin_code,
                "amount": gift_card_data.amount,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "message": "Gift card created successfully"
            }
            
        except Exception as e:
            logger.error(f"Gift card creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def check_balance(self, card_number: str, pin_code: Optional[str] = None) -> Dict[str, Any]:
        """Check gift card balance"""
        try:
            # Find gift card
            query = self.db.query(GiftCard).filter(GiftCard.card_number == card_number)
            
            if pin_code:
                query = query.filter(GiftCard.pin_code == pin_code)
            
            gift_card = query.first()
            
            if not gift_card:
                return {"success": False, "error": "Gift card not found or invalid PIN"}
            
            # Check if expired
            if gift_card.expires_at and datetime.now() > gift_card.expires_at:
                if gift_card.status != GiftCardStatus.EXPIRED:
                    gift_card.status = GiftCardStatus.EXPIRED
                    self.db.commit()
                
                return {"success": False, "error": "Gift card has expired"}
            
            # Check if cancelled
            if gift_card.status == GiftCardStatus.CANCELLED:
                return {"success": False, "error": "Gift card has been cancelled"}
            
            return {
                "success": True,
                "card_number": card_number,
                "current_balance": gift_card.current_balance,
                "initial_amount": gift_card.initial_amount,
                "status": gift_card.status,
                "expires_at": gift_card.expires_at.isoformat() if gift_card.expires_at else None,
                "last_used_at": gift_card.last_used_at.isoformat() if gift_card.last_used_at else None
            }
            
        except Exception as e:
            logger.error(f"Gift card balance check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def redeem_gift_card(self, card_number: str, amount: float, sale_id: Optional[int] = None, 
                              pin_code: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Redeem gift card for purchase"""
        try:
            # Find gift card
            query = self.db.query(GiftCard).filter(GiftCard.card_number == card_number)
            
            if pin_code:
                query = query.filter(GiftCard.pin_code == pin_code)
            
            gift_card = query.first()
            
            if not gift_card:
                return {"success": False, "error": "Gift card not found or invalid PIN"}
            
            # Validate gift card status
            if gift_card.status == GiftCardStatus.CANCELLED:
                return {"success": False, "error": "Gift card has been cancelled"}
            
            if gift_card.status == GiftCardStatus.EXPIRED:
                return {"success": False, "error": "Gift card has expired"}
            
            # Check expiry
            if gift_card.expires_at and datetime.now() > gift_card.expires_at:
                gift_card.status = GiftCardStatus.EXPIRED
                self.db.commit()
                return {"success": False, "error": "Gift card has expired"}
            
            # Check sufficient balance
            if gift_card.current_balance < amount:
                return {
                    "success": False, 
                    "error": f"Insufficient balance. Available: ${gift_card.current_balance:.2f}"
                }
            
            # Process redemption
            balance_before = gift_card.current_balance
            gift_card.current_balance -= amount
            gift_card.last_used_at = datetime.now()
            
            # Update status
            if gift_card.current_balance == 0:
                gift_card.status = GiftCardStatus.REDEEMED
            else:
                gift_card.status = GiftCardStatus.PARTIALLY_USED
            
            # Create transaction record
            transaction = GiftCardTransaction(
                gift_card_id=gift_card.gift_card_id,
                sale_id=sale_id,
                transaction_type='redemption',
                amount=-amount,  # Negative for redemption
                balance_before=balance_before,
                balance_after=gift_card.current_balance,
                description=f'Gift card redemption for ${amount:.2f}',
                created_by=user_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            return {
                "success": True,
                "redeemed_amount": amount,
                "remaining_balance": gift_card.current_balance,
                "transaction_id": transaction.transaction_id,
                "message": "Gift card redeemed successfully"
            }
            
        except Exception as e:
            logger.error(f"Gift card redemption failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def refund_to_gift_card(self, card_number: str, amount: float, reason: str, 
                                 user_id: Optional[int] = None) -> Dict[str, Any]:
        """Add refund amount to gift card"""
        try:
            gift_card = self.db.query(GiftCard).filter(
                GiftCard.card_number == card_number
            ).first()
            
            if not gift_card:
                return {"success": False, "error": "Gift card not found"}
            
            # Add amount to balance
            balance_before = gift_card.current_balance
            gift_card.current_balance += amount
            
            # Update status if was fully redeemed
            if gift_card.status == GiftCardStatus.REDEEMED:
                gift_card.status = GiftCardStatus.PARTIALLY_USED
            
            # Create transaction record
            transaction = GiftCardTransaction(
                gift_card_id=gift_card.gift_card_id,
                transaction_type='refund',
                amount=amount,
                balance_before=balance_before,
                balance_after=gift_card.current_balance,
                description=f'Refund: {reason}',
                created_by=user_id
            )
            
            self.db.add(transaction)
            self.db.commit()
            
            return {
                "success": True,
                "refund_amount": amount,
                "new_balance": gift_card.current_balance,
                "message": "Refund added to gift card successfully"
            }
            
        except Exception as e:
            logger.error(f"Gift card refund failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_gift_card_history(self, card_number: str, pin_code: Optional[str] = None) -> Dict[str, Any]:
        """Get gift card transaction history"""
        try:
            # Find gift card
            query = self.db.query(GiftCard).filter(GiftCard.card_number == card_number)
            
            if pin_code:
                query = query.filter(GiftCard.pin_code == pin_code)
            
            gift_card = query.first()
            
            if not gift_card:
                return {"success": False, "error": "Gift card not found or invalid PIN"}
            
            # Get transactions
            transactions_query = """
            SELECT 
                transaction_type,
                amount,
                balance_before,
                balance_after,
                description,
                created_at
            FROM gift_card_transactions
            WHERE gift_card_id = :gift_card_id
            ORDER BY created_at DESC
            """
            
            result = self.db.execute(text(transactions_query), {
                'gift_card_id': gift_card.gift_card_id
            })
            transactions = [dict(row) for row in result.fetchall()]
            
            return {
                "success": True,
                "card_number": card_number,
                "current_balance": gift_card.current_balance,
                "initial_amount": gift_card.initial_amount,
                "status": gift_card.status,
                "created_at": gift_card.created_at.isoformat(),
                "expires_at": gift_card.expires_at.isoformat() if gift_card.expires_at else None,
                "transactions": transactions
            }
            
        except Exception as e:
            logger.error(f"Gift card history retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_gift_card_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get gift card analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Gift card summary
            summary_query = """
            SELECT 
                COUNT(*) as total_cards,
                SUM(initial_amount) as total_issued,
                SUM(current_balance) as total_outstanding,
                SUM(initial_amount - current_balance) as total_redeemed,
                AVG(initial_amount) as avg_card_value
            FROM gift_cards
            WHERE created_at >= :start_date
            """
            
            result = self.db.execute(text(summary_query), {'start_date': start_date})
            summary = dict(result.fetchone())
            
            # Status breakdown
            status_query = """
            SELECT 
                status,
                COUNT(*) as count,
                SUM(current_balance) as total_balance
            FROM gift_cards
            WHERE created_at >= :start_date
            GROUP BY status
            """
            
            status_result = self.db.execute(text(status_query), {'start_date': start_date})
            status_breakdown = [dict(row) for row in status_result.fetchall()]
            
            # Daily trends
            daily_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as cards_issued,
                SUM(initial_amount) as amount_issued
            FROM gift_cards
            WHERE created_at >= :start_date
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            
            daily_result = self.db.execute(text(daily_query), {'start_date': start_date})
            daily_trends = [dict(row) for row in daily_result.fetchall()]
            
            # Redemption analytics
            redemption_query = """
            SELECT 
                COUNT(*) as redemption_count,
                SUM(ABS(amount)) as total_redeemed,
                AVG(ABS(amount)) as avg_redemption
            FROM gift_card_transactions
            WHERE transaction_type = 'redemption'
            AND created_at >= :start_date
            """
            
            redemption_result = self.db.execute(text(redemption_query), {'start_date': start_date})
            redemption_stats = dict(redemption_result.fetchone())
            
            return {
                "success": True,
                "period_days": days_back,
                "summary": {
                    "total_cards": summary['total_cards'] or 0,
                    "total_issued": float(summary['total_issued'] or 0),
                    "total_outstanding": float(summary['total_outstanding'] or 0),
                    "total_redeemed": float(summary['total_redeemed'] or 0),
                    "avg_card_value": float(summary['avg_card_value'] or 0),
                    "redemption_rate": float((summary['total_redeemed'] or 0) / (summary['total_issued'] or 1) * 100)
                },
                "status_breakdown": status_breakdown,
                "daily_trends": daily_trends,
                "redemption_stats": redemption_stats,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Gift card analytics failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_gift_card_email(self, gift_card: GiftCard) -> None:
        """Send gift card via email"""
        try:
            # This would integrate with your email system
            # For now, just log the action
            logger.info(f"Gift card email sent to {gift_card.recipient_email} for card {gift_card.card_number}")
            
            # In a real implementation, you would:
            # 1. Generate a beautiful HTML email template
            # 2. Include the gift card details
            # 3. Add any personal message
            # 4. Send via your email service
            
        except Exception as e:
            logger.error(f"Gift card email sending failed: {e}")

def create_gift_card_manager(db: Session) -> GiftCardManager:
    """Factory function to create gift card manager"""
    return GiftCardManager(db)
