"""
Two-Factor Authentication Module
Implements TOTP-based 2FA for enhanced security
"""

import os
import logging
import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enhanced_main import Base
import secrets
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

logger = logging.getLogger(__name__)

# Database Models
class TwoFactorAuth(Base):
    __tablename__ = "two_factor_auth"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    secret_key = Column(String(32))  # Base32 encoded secret
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(String(500))  # JSON string of backup codes
    created_at = Column(DateTime, server_default=func.now())
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="two_factor_auth")

class TwoFactorBackupCode(Base):
    __tablename__ = "two_factor_backup_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    code = Column(String(10), unique=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    username = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    success = Column(Boolean)
    failure_reason = Column(String(200), nullable=True)
    two_factor_required = Column(Boolean, default=False)
    two_factor_success = Column(Boolean, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")

# Pydantic Models
class TwoFactorSetup(BaseModel):
    qr_code: str
    secret_key: str
    backup_codes: list[str]

class TwoFactorVerify(BaseModel):
    token: str

class TwoFactorEnable(BaseModel):
    token: str

class TwoFactorBackupVerify(BaseModel):
    backup_code: str

class TwoFactorAuthManager:
    """Two-Factor Authentication Manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.company_name = os.environ.get('COMPANY_NAME', 'Electronics Store')
    
    async def setup_2fa(self, user_id: int) -> Dict[str, Any]:
        """Setup 2FA for a user"""
        try:
            # Check if 2FA already exists
            existing_2fa = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id
            ).first()
            
            if existing_2fa and existing_2fa.is_enabled:
                return {"success": False, "error": "2FA is already enabled"}
            
            # Get user details
            user_query = "SELECT username, email FROM users WHERE user_id = :user_id"
            result = self.db.execute(text(user_query), {'user_id': user_id})
            user = result.fetchone()
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Generate secret key
            secret = pyotp.random_base32()
            
            # Create TOTP instance
            totp = pyotp.TOTP(secret)
            
            # Generate QR code
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name=self.company_name
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(5).upper() for _ in range(10)]
            
            # Save or update 2FA record
            if existing_2fa:
                existing_2fa.secret_key = secret
                existing_2fa.backup_codes = ','.join(backup_codes)
                two_factor_auth = existing_2fa
            else:
                two_factor_auth = TwoFactorAuth(
                    user_id=user_id,
                    secret_key=secret,
                    backup_codes=','.join(backup_codes),
                    is_enabled=False
                )
                self.db.add(two_factor_auth)
            
            # Save backup codes individually
            self.db.query(TwoFactorBackupCode).filter(
                TwoFactorBackupCode.user_id == user_id
            ).delete()
            
            for code in backup_codes:
                backup_code = TwoFactorBackupCode(
                    user_id=user_id,
                    code=code
                )
                self.db.add(backup_code)
            
            self.db.commit()
            
            return {
                "success": True,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "secret_key": secret,
                "backup_codes": backup_codes,
                "manual_entry_key": secret
            }
            
        except Exception as e:
            logger.error(f"2FA setup failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def enable_2fa(self, user_id: int, token: str) -> Dict[str, Any]:
        """Enable 2FA after verifying initial token"""
        try:
            # Get 2FA record
            two_factor_auth = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id
            ).first()
            
            if not two_factor_auth:
                return {"success": False, "error": "2FA not set up"}
            
            if two_factor_auth.is_enabled:
                return {"success": False, "error": "2FA is already enabled"}
            
            # Verify token
            totp = pyotp.TOTP(two_factor_auth.secret_key)
            if not totp.verify(token, valid_window=1):
                return {"success": False, "error": "Invalid token"}
            
            # Enable 2FA
            two_factor_auth.is_enabled = True
            two_factor_auth.last_used = datetime.now()
            self.db.commit()
            
            # Log the enablement
            await self._log_2fa_event(user_id, "2FA_ENABLED", "2FA enabled successfully")
            
            return {
                "success": True,
                "message": "Two-factor authentication enabled successfully"
            }
            
        except Exception as e:
            logger.error(f"2FA enable failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_2fa(self, user_id: int, token: str) -> Dict[str, Any]:
        """Verify 2FA token"""
        try:
            # Get 2FA record
            two_factor_auth = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id,
                TwoFactorAuth.is_enabled == True
            ).first()
            
            if not two_factor_auth:
                return {"success": False, "error": "2FA not enabled"}
            
            # Verify TOTP token
            totp = pyotp.TOTP(two_factor_auth.secret_key)
            if totp.verify(token, valid_window=1):
                two_factor_auth.last_used = datetime.now()
                self.db.commit()
                
                await self._log_2fa_event(user_id, "2FA_SUCCESS", "2FA verification successful")
                
                return {
                    "success": True,
                    "message": "2FA verification successful"
                }
            else:
                await self._log_2fa_event(user_id, "2FA_FAILED", "Invalid 2FA token")
                return {"success": False, "error": "Invalid token"}
            
        except Exception as e:
            logger.error(f"2FA verification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_backup_code(self, user_id: int, backup_code: str) -> Dict[str, Any]:
        """Verify backup code"""
        try:
            # Find unused backup code
            backup_code_record = self.db.query(TwoFactorBackupCode).filter(
                TwoFactorBackupCode.user_id == user_id,
                TwoFactorBackupCode.code == backup_code.upper(),
                TwoFactorBackupCode.is_used == False
            ).first()
            
            if not backup_code_record:
                await self._log_2fa_event(user_id, "BACKUP_CODE_FAILED", "Invalid backup code")
                return {"success": False, "error": "Invalid or used backup code"}
            
            # Mark backup code as used
            backup_code_record.is_used = True
            backup_code_record.used_at = datetime.now()
            self.db.commit()
            
            await self._log_2fa_event(user_id, "BACKUP_CODE_SUCCESS", "Backup code used successfully")
            
            return {
                "success": True,
                "message": "Backup code verification successful",
                "warning": "This backup code cannot be used again"
            }
            
        except Exception as e:
            logger.error(f"Backup code verification failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def disable_2fa(self, user_id: int, token: str) -> Dict[str, Any]:
        """Disable 2FA"""
        try:
            # Verify current token first
            verify_result = await self.verify_2fa(user_id, token)
            if not verify_result["success"]:
                return verify_result
            
            # Get 2FA record
            two_factor_auth = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id
            ).first()
            
            if two_factor_auth:
                two_factor_auth.is_enabled = False
                
                # Remove backup codes
                self.db.query(TwoFactorBackupCode).filter(
                    TwoFactorBackupCode.user_id == user_id
                ).delete()
                
                self.db.commit()
                
                await self._log_2fa_event(user_id, "2FA_DISABLED", "2FA disabled successfully")
                
                return {
                    "success": True,
                    "message": "Two-factor authentication disabled"
                }
            else:
                return {"success": False, "error": "2FA not found"}
            
        except Exception as e:
            logger.error(f"2FA disable failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def regenerate_backup_codes(self, user_id: int, token: str) -> Dict[str, Any]:
        """Regenerate backup codes"""
        try:
            # Verify current token first
            verify_result = await self.verify_2fa(user_id, token)
            if not verify_result["success"]:
                return verify_result
            
            # Generate new backup codes
            new_backup_codes = [secrets.token_hex(5).upper() for _ in range(10)]
            
            # Remove old backup codes
            self.db.query(TwoFactorBackupCode).filter(
                TwoFactorBackupCode.user_id == user_id
            ).delete()
            
            # Add new backup codes
            for code in new_backup_codes:
                backup_code = TwoFactorBackupCode(
                    user_id=user_id,
                    code=code
                )
                self.db.add(backup_code)
            
            # Update 2FA record
            two_factor_auth = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id
            ).first()
            
            if two_factor_auth:
                two_factor_auth.backup_codes = ','.join(new_backup_codes)
            
            self.db.commit()
            
            await self._log_2fa_event(user_id, "BACKUP_CODES_REGENERATED", "Backup codes regenerated")
            
            return {
                "success": True,
                "backup_codes": new_backup_codes,
                "message": "New backup codes generated"
            }
            
        except Exception as e:
            logger.error(f"Backup code regeneration failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_2fa_status(self, user_id: int) -> Dict[str, Any]:
        """Get 2FA status for user"""
        try:
            two_factor_auth = self.db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user_id
            ).first()
            
            if not two_factor_auth:
                return {
                    "success": True,
                    "enabled": False,
                    "setup_required": True
                }
            
            # Count unused backup codes
            unused_backup_codes = self.db.query(TwoFactorBackupCode).filter(
                TwoFactorBackupCode.user_id == user_id,
                TwoFactorBackupCode.is_used == False
            ).count()
            
            return {
                "success": True,
                "enabled": two_factor_auth.is_enabled,
                "setup_required": not two_factor_auth.is_enabled,
                "last_used": two_factor_auth.last_used.isoformat() if two_factor_auth.last_used else None,
                "unused_backup_codes": unused_backup_codes,
                "created_at": two_factor_auth.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"2FA status check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_login_security(self, username: str, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """Check login security and detect suspicious activity"""
        try:
            # Check recent failed attempts
            recent_failures = self.db.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.success == False,
                LoginAttempt.created_at >= datetime.now() - timedelta(minutes=15)
            ).count()
            
            # Check attempts from different IPs
            different_ip_attempts = self.db.query(LoginAttempt).filter(
                LoginAttempt.username == username,
                LoginAttempt.ip_address != ip_address,
                LoginAttempt.created_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            # Determine risk level
            risk_level = "low"
            risk_factors = []
            
            if recent_failures >= 3:
                risk_level = "high"
                risk_factors.append("Multiple recent failed attempts")
            elif recent_failures >= 1:
                risk_level = "medium"
                risk_factors.append("Recent failed attempts")
            
            if different_ip_attempts > 0:
                risk_level = "high"
                risk_factors.append("Login attempts from different IP addresses")
            
            return {
                "success": True,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "recent_failures": recent_failures,
                "require_2fa": risk_level in ["medium", "high"]
            }
            
        except Exception as e:
            logger.error(f"Login security check failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def log_login_attempt(self, username: str, user_id: Optional[int], ip_address: str, 
                               user_agent: str, success: bool, failure_reason: Optional[str] = None,
                               two_factor_required: bool = False, two_factor_success: Optional[bool] = None) -> None:
        """Log login attempt"""
        try:
            login_attempt = LoginAttempt(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
                two_factor_required=two_factor_required,
                two_factor_success=two_factor_success
            )
            
            self.db.add(login_attempt)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Login attempt logging failed: {e}")
    
    async def _log_2fa_event(self, user_id: int, event_type: str, details: str) -> None:
        """Log 2FA events for audit trail"""
        try:
            audit_query = """
            INSERT INTO audit_logs (table_name, record_id, action, details, user_id, created_at)
            VALUES ('two_factor_auth', :user_id, :event_type, :details, :user_id, CURRENT_TIMESTAMP)
            """
            
            self.db.execute(text(audit_query), {
                'user_id': user_id,
                'event_type': event_type,
                'details': details
            })
            self.db.commit()
            
        except Exception as e:
            logger.error(f"2FA event logging failed: {e}")

def create_2fa_manager(db: Session) -> TwoFactorAuthManager:
    """Factory function to create 2FA manager"""
    return TwoFactorAuthManager(db)
