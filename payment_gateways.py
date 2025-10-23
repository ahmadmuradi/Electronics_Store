"""
Payment Gateway Integration Module
Handles Stripe and PayPal payment processing
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
import stripe
import paypalrestsdk
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enum import Enum
from enhanced_main import Base

logger = logging.getLogger(__name__)

# Configure payment gateways
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

paypalrestsdk.configure({
    "mode": os.environ.get('PAYPAL_MODE', 'sandbox'),  # sandbox or live
    "client_id": os.environ.get('PAYPAL_CLIENT_ID', ''),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET', '')
})

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(str, Enum):
    STRIPE_CARD = "stripe_card"
    STRIPE_BANK = "stripe_bank"
    PAYPAL = "paypal"
    CASH = "cash"
    GIFT_CARD = "gift_card"

# Database Models
class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String(100), unique=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    
    amount = Column(Float)
    currency = Column(String(3), default="USD")
    payment_method = Column(SQLEnum(PaymentMethod))
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Gateway-specific fields
    stripe_payment_intent_id = Column(String(200), nullable=True)
    paypal_payment_id = Column(String(200), nullable=True)
    gateway_response = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    sale = relationship("Sale")
    customer = relationship("Customer")

class PaymentRefund(Base):
    __tablename__ = "payment_refunds"
    
    refund_id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.payment_id"))
    refund_reference = Column(String(100), unique=True, index=True)
    
    amount = Column(Float)
    reason = Column(String(500))
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    gateway_refund_id = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    payment = relationship("Payment")

# Pydantic Models
class PaymentCreate(BaseModel):
    sale_id: int
    amount: float
    currency: str = "USD"
    payment_method: PaymentMethod
    customer_email: Optional[str] = None

class PaymentIntent(BaseModel):
    client_secret: str
    payment_id: int
    amount: float
    currency: str

class RefundCreate(BaseModel):
    payment_id: int
    amount: Optional[float] = None  # None for full refund
    reason: str

class StripePaymentProcessor:
    """Stripe payment processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_payment_intent(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """Create Stripe payment intent"""
        try:
            if not stripe.api_key:
                return {"success": False, "error": "Stripe not configured"}
            
            # Create payment record
            payment_ref = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            payment = Payment(
                payment_reference=payment_ref,
                sale_id=payment_data.sale_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=payment_data.payment_method,
                status=PaymentStatus.PENDING
            )
            
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment_data.amount * 100),  # Stripe uses cents
                currency=payment_data.currency.lower(),
                metadata={
                    'payment_id': payment.payment_id,
                    'sale_id': payment_data.sale_id
                },
                automatic_payment_methods={'enabled': True}
            )
            
            # Update payment with Stripe intent ID
            payment.stripe_payment_intent_id = intent.id
            self.db.commit()
            
            return {
                "success": True,
                "payment_id": payment.payment_id,
                "client_secret": intent.client_secret,
                "publishable_key": STRIPE_PUBLISHABLE_KEY
            }
            
        except Exception as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm Stripe payment"""
        try:
            # Retrieve payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find local payment record
            payment = self.db.query(Payment).filter(
                Payment.stripe_payment_intent_id == payment_intent_id
            ).first()
            
            if not payment:
                return {"success": False, "error": "Payment not found"}
            
            # Update payment status based on Stripe status
            if intent.status == 'succeeded':
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.now()
            elif intent.status == 'requires_payment_method':
                payment.status = PaymentStatus.FAILED
            elif intent.status == 'canceled':
                payment.status = PaymentStatus.CANCELLED
            
            payment.gateway_response = str(intent)
            self.db.commit()
            
            return {
                "success": True,
                "payment_id": payment.payment_id,
                "status": payment.status,
                "amount": payment.amount
            }
            
        except Exception as e:
            logger.error(f"Stripe payment confirmation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_refund(self, refund_data: RefundCreate) -> Dict[str, Any]:
        """Create Stripe refund"""
        try:
            # Get payment record
            payment = self.db.query(Payment).filter(
                Payment.payment_id == refund_data.payment_id
            ).first()
            
            if not payment or not payment.stripe_payment_intent_id:
                return {"success": False, "error": "Payment not found or not Stripe payment"}
            
            # Determine refund amount
            refund_amount = refund_data.amount or payment.amount
            
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=int(refund_amount * 100),  # Stripe uses cents
                reason='requested_by_customer',
                metadata={'payment_id': payment.payment_id}
            )
            
            # Create refund record
            refund_ref = f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            payment_refund = PaymentRefund(
                payment_id=payment.payment_id,
                refund_reference=refund_ref,
                amount=refund_amount,
                reason=refund_data.reason,
                status=PaymentStatus.COMPLETED if refund.status == 'succeeded' else PaymentStatus.PENDING,
                gateway_refund_id=refund.id,
                processed_at=datetime.now() if refund.status == 'succeeded' else None
            )
            
            self.db.add(payment_refund)
            
            # Update payment status
            if refund_amount >= payment.amount:
                payment.status = PaymentStatus.REFUNDED
            else:
                payment.status = PaymentStatus.PARTIALLY_REFUNDED
            
            self.db.commit()
            
            return {
                "success": True,
                "refund_id": payment_refund.refund_id,
                "amount": refund_amount,
                "status": payment_refund.status
            }
            
        except Exception as e:
            logger.error(f"Stripe refund creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

class PayPalPaymentProcessor:
    """PayPal payment processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_payment(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """Create PayPal payment"""
        try:
            if not paypalrestsdk.api.default().client_id:
                return {"success": False, "error": "PayPal not configured"}
            
            # Create payment record
            payment_ref = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            payment = Payment(
                payment_reference=payment_ref,
                sale_id=payment_data.sale_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=PaymentMethod.PAYPAL,
                status=PaymentStatus.PENDING
            )
            
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            
            # Create PayPal payment
            paypal_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"{os.environ.get('BASE_URL', 'http://localhost:8001')}/payments/paypal/success",
                    "cancel_url": f"{os.environ.get('BASE_URL', 'http://localhost:8001')}/payments/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"Order #{payment_data.sale_id}",
                            "sku": f"sale_{payment_data.sale_id}",
                            "price": str(payment_data.amount),
                            "currency": payment_data.currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(payment_data.amount),
                        "currency": payment_data.currency
                    },
                    "description": f"Payment for sale #{payment_data.sale_id}"
                }]
            })
            
            if paypal_payment.create():
                # Update payment with PayPal payment ID
                payment.paypal_payment_id = paypal_payment.id
                self.db.commit()
                
                # Get approval URL
                approval_url = None
                for link in paypal_payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    "success": True,
                    "payment_id": payment.payment_id,
                    "paypal_payment_id": paypal_payment.id,
                    "approval_url": approval_url
                }
            else:
                logger.error(f"PayPal payment creation failed: {paypal_payment.error}")
                return {"success": False, "error": str(paypal_payment.error)}
            
        except Exception as e:
            logger.error(f"PayPal payment creation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def execute_payment(self, payment_id: str, payer_id: str) -> Dict[str, Any]:
        """Execute PayPal payment"""
        try:
            # Find local payment record
            payment = self.db.query(Payment).filter(
                Payment.paypal_payment_id == payment_id
            ).first()
            
            if not payment:
                return {"success": False, "error": "Payment not found"}
            
            # Execute PayPal payment
            paypal_payment = paypalrestsdk.Payment.find(payment_id)
            
            if paypal_payment.execute({"payer_id": payer_id}):
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.now()
                payment.gateway_response = str(paypal_payment)
                self.db.commit()
                
                return {
                    "success": True,
                    "payment_id": payment.payment_id,
                    "status": payment.status,
                    "amount": payment.amount
                }
            else:
                payment.status = PaymentStatus.FAILED
                payment.gateway_response = str(paypal_payment.error)
                self.db.commit()
                
                return {"success": False, "error": str(paypal_payment.error)}
            
        except Exception as e:
            logger.error(f"PayPal payment execution failed: {e}")
            return {"success": False, "error": str(e)}

class PaymentGatewayManager:
    """Main payment gateway manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stripe = StripePaymentProcessor(db)
        self.paypal = PayPalPaymentProcessor(db)
    
    async def create_payment(self, payment_data: PaymentCreate) -> Dict[str, Any]:
        """Create payment based on method"""
        try:
            if payment_data.payment_method in [PaymentMethod.STRIPE_CARD, PaymentMethod.STRIPE_BANK]:
                return await self.stripe.create_payment_intent(payment_data)
            elif payment_data.payment_method == PaymentMethod.PAYPAL:
                return await self.paypal.create_payment(payment_data)
            else:
                return {"success": False, "error": "Unsupported payment method"}
                
        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_payment_status(self, payment_id: int) -> Dict[str, Any]:
        """Get payment status"""
        try:
            payment = self.db.query(Payment).filter(
                Payment.payment_id == payment_id
            ).first()
            
            if not payment:
                return {"success": False, "error": "Payment not found"}
            
            return {
                "success": True,
                "payment_id": payment.payment_id,
                "status": payment.status,
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method,
                "created_at": payment.created_at.isoformat(),
                "processed_at": payment.processed_at.isoformat() if payment.processed_at else None
            }
            
        except Exception as e:
            logger.error(f"Payment status retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_refund(self, refund_data: RefundCreate) -> Dict[str, Any]:
        """Create refund"""
        try:
            payment = self.db.query(Payment).filter(
                Payment.payment_id == refund_data.payment_id
            ).first()
            
            if not payment:
                return {"success": False, "error": "Payment not found"}
            
            if payment.payment_method in [PaymentMethod.STRIPE_CARD, PaymentMethod.STRIPE_BANK]:
                return await self.stripe.create_refund(refund_data)
            elif payment.payment_method == PaymentMethod.PAYPAL:
                # PayPal refund implementation would go here
                return {"success": False, "error": "PayPal refunds not implemented yet"}
            else:
                return {"success": False, "error": "Refund not supported for this payment method"}
                
        except Exception as e:
            logger.error(f"Refund creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_payment_analytics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get payment analytics"""
        try:
            start_date = datetime.now() - timedelta(days=days_back)
            
            # Payment summary
            summary_query = """
            SELECT 
                payment_method,
                status,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM payments
            WHERE created_at >= :start_date
            GROUP BY payment_method, status
            ORDER BY total_amount DESC
            """
            
            result = self.db.execute(text(summary_query), {'start_date': start_date})
            payment_summary = [dict(row) for row in result.fetchall()]
            
            # Daily trends
            daily_query = """
            SELECT 
                DATE(created_at) as payment_date,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM payments
            WHERE created_at >= :start_date
            AND status = 'completed'
            GROUP BY DATE(created_at)
            ORDER BY payment_date
            """
            
            daily_result = self.db.execute(text(daily_query), {'start_date': start_date})
            daily_trends = [dict(row) for row in daily_result.fetchall()]
            
            # Calculate totals
            total_payments = sum(item['count'] for item in payment_summary if item['status'] == 'completed')
            total_amount = sum(item['total_amount'] for item in payment_summary if item['status'] == 'completed')
            
            return {
                "success": True,
                "period_days": days_back,
                "summary": {
                    "total_payments": total_payments,
                    "total_amount": float(total_amount) if total_amount else 0,
                    "avg_payment": float(total_amount / total_payments) if total_payments > 0 else 0
                },
                "payment_methods": payment_summary,
                "daily_trends": daily_trends,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Payment analytics failed: {e}")
            return {"success": False, "error": str(e)}

def create_payment_gateway_manager(db: Session) -> PaymentGatewayManager:
    """Factory function to create payment gateway manager"""
    return PaymentGatewayManager(db)
