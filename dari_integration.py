"""
Dari Language Integration Module
Provides Dari language support with basic translations and RTL support
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from multi_language import create_multi_language_manager, TranslationCreate

logger = logging.getLogger(__name__)

class DariLanguageIntegrator:
    """Dari language integration and translation helper"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_manager = create_multi_language_manager(db)
        self.language_code = 'prs'  # ISO 639-3 code for Dari
        
    async def setup_dari_language(self) -> Dict[str, Any]:
        """Setup Dari language with basic translations"""
        try:
            # Basic UI translations in Dari
            basic_translations = {
                # Navigation and Menu
                "nav.home": "خانه",
                "nav.products": "محصولات",
                "nav.inventory": "موجودات",
                "nav.sales": "فروش",
                "nav.customers": "مشتریان",
                "nav.reports": "گزارشات",
                "nav.settings": "تنظیمات",
                "nav.logout": "خروج",
                
                # Common UI Elements
                "ui.save": "ذخیره",
                "ui.cancel": "لغو",
                "ui.delete": "حذف",
                "ui.edit": "ویرایش",
                "ui.add": "اضافه کردن",
                "ui.search": "جستجو",
                "ui.filter": "فیلتر",
                "ui.export": "صادرات",
                "ui.import": "واردات",
                "ui.print": "چاپ",
                "ui.close": "بستن",
                "ui.submit": "ارسال",
                "ui.reset": "بازنشانی",
                "ui.confirm": "تأیید",
                "ui.yes": "بله",
                "ui.no": "نه",
                "ui.ok": "باشه",
                "ui.loading": "در حال بارگذاری...",
                "ui.error": "خطا",
                "ui.success": "موفقیت",
                "ui.warning": "هشدار",
                "ui.info": "اطلاعات",
                
                # Product Management
                "product.name": "نام محصول",
                "product.description": "توضیحات",
                "product.price": "قیمت",
                "product.cost": "هزینه",
                "product.sku": "کد محصول",
                "product.category": "دسته‌بندی",
                "product.stock": "موجودی",
                "product.barcode": "بارکد",
                "product.brand": "برند",
                "product.model": "مدل",
                "product.warranty": "گارانتی",
                "product.supplier": "تأمین‌کننده",
                "product.location": "مکان",
                "product.status": "وضعیت",
                "product.active": "فعال",
                "product.inactive": "غیرفعال",
                "product.discontinued": "متوقف شده",
                
                # Inventory Management
                "inventory.stock_level": "سطح موجودی",
                "inventory.reorder_level": "سطح سفارش مجدد",
                "inventory.max_stock": "حداکثر موجودی",
                "inventory.min_stock": "حداقل موجودی",
                "inventory.in_stock": "موجود",
                "inventory.out_of_stock": "ناموجود",
                "inventory.low_stock": "موجودی کم",
                "inventory.adjustment": "تعدیل موجودی",
                "inventory.transfer": "انتقال",
                "inventory.receive": "دریافت",
                "inventory.issue": "صدور",
                
                # Sales and Orders
                "sale.customer": "مشتری",
                "sale.date": "تاریخ فروش",
                "sale.amount": "مبلغ",
                "sale.quantity": "تعداد",
                "sale.total": "مجموع",
                "sale.subtotal": "جمع جزء",
                "sale.tax": "مالیات",
                "sale.discount": "تخفیف",
                "sale.payment_method": "روش پرداخت",
                "sale.cash": "نقدی",
                "sale.card": "کارت",
                "sale.credit": "اعتبار",
                "sale.invoice": "فاکتور",
                "sale.receipt": "رسید",
                "sale.refund": "بازپرداخت",
                "sale.return": "برگشت",
                
                # Customer Management
                "customer.name": "نام مشتری",
                "customer.email": "ایمیل",
                "customer.phone": "تلفن",
                "customer.address": "آدرس",
                "customer.city": "شهر",
                "customer.country": "کشور",
                "customer.postal_code": "کد پستی",
                "customer.registration_date": "تاریخ ثبت‌نام",
                "customer.total_purchases": "کل خریدها",
                "customer.loyalty_points": "امتیاز وفاداری",
                
                # Reports and Analytics
                "report.sales_report": "گزارش فروش",
                "report.inventory_report": "گزارش موجودی",
                "report.customer_report": "گزارش مشتریان",
                "report.profit_loss": "سود و زیان",
                "report.daily": "روزانه",
                "report.weekly": "هفتگی",
                "report.monthly": "ماهانه",
                "report.yearly": "سالانه",
                "report.date_range": "بازه تاریخ",
                "report.from_date": "از تاریخ",
                "report.to_date": "تا تاریخ",
                "report.generate": "تولید گزارش",
                
                # User Management
                "user.username": "نام کاربری",
                "user.password": "رمز عبور",
                "user.email": "ایمیل",
                "user.role": "نقش",
                "user.admin": "مدیر",
                "user.manager": "مدیر فروش",
                "user.cashier": "صندوقدار",
                "user.last_login": "آخرین ورود",
                "user.status": "وضعیت",
                "user.active": "فعال",
                "user.inactive": "غیرفعال",
                
                # Settings and Configuration
                "settings.general": "عمومی",
                "settings.company": "شرکت",
                "settings.store": "فروشگاه",
                "settings.tax": "مالیات",
                "settings.currency": "واحد پول",
                "settings.language": "زبان",
                "settings.timezone": "منطقه زمانی",
                "settings.backup": "پشتیبان‌گیری",
                "settings.restore": "بازیابی",
                "settings.security": "امنیت",
                
                # Payment and Gift Cards
                "payment.method": "روش پرداخت",
                "payment.amount": "مبلغ پرداخت",
                "payment.status": "وضعیت پرداخت",
                "payment.pending": "در انتظار",
                "payment.completed": "تکمیل شده",
                "payment.failed": "ناموفق",
                "payment.refunded": "بازپرداخت شده",
                "giftcard.number": "شماره کارت هدیه",
                "giftcard.balance": "موجودی کارت هدیه",
                "giftcard.redeem": "استفاده از کارت هدیه",
                "giftcard.create": "ایجاد کارت هدیه",
                
                # Two-Factor Authentication
                "2fa.setup": "راه‌اندازی احراز هویت دو مرحله‌ای",
                "2fa.enable": "فعال‌سازی 2FA",
                "2fa.disable": "غیرفعال‌سازی 2FA",
                "2fa.verify": "تأیید کد",
                "2fa.backup_codes": "کدهای پشتیبان",
                "2fa.qr_code": "کد QR",
                "2fa.authenticator": "برنامه احراز هویت",
                
                # Multi-language
                "language.dari": "دری",
                "language.english": "انگلیسی",
                "language.arabic": "عربی",
                "language.persian": "فارسی",
                "language.urdu": "اردو",
                "language.pashto": "پشتو",
                
                # Time and Date
                "date.today": "امروز",
                "date.yesterday": "دیروز",
                "date.tomorrow": "فردا",
                "date.this_week": "این هفته",
                "date.this_month": "این ماه",
                "date.this_year": "امسال",
                
                # Status Messages
                "status.online": "آنلاین",
                "status.offline": "آفلاین",
                "status.connected": "متصل",
                "status.disconnected": "قطع شده",
                "status.syncing": "همگام‌سازی",
                "status.synced": "همگام‌سازی شده",
                
                # Electronics Categories (Common in Afghanistan)
                "category.mobile_phones": "تلفن همراه",
                "category.computers": "کامپیوتر",
                "category.laptops": "لپ‌تاپ",
                "category.tablets": "تبلت",
                "category.accessories": "لوازم جانبی",
                "category.chargers": "شارژر",
                "category.cables": "کابل",
                "category.headphones": "هدفون",
                "category.speakers": "بلندگو",
                "category.cameras": "دوربین",
                "category.memory_cards": "کارت حافظه",
                "category.power_banks": "پاوربانک",
                "category.smart_watches": "ساعت هوشمند",
                "category.gaming": "بازی",
                "category.networking": "شبکه",
                
                # Common Electronics Brands
                "brand.samsung": "سامسونگ",
                "brand.apple": "اپل",
                "brand.huawei": "هواوی",
                "brand.xiaomi": "شیائومی",
                "brand.oppo": "اوپو",
                "brand.vivo": "ویوو",
                "brand.nokia": "نوکیا",
                "brand.sony": "سونی",
                "brand.lg": "ال‌جی",
                
                # Error Messages
                "error.not_found": "یافت نشد",
                "error.access_denied": "دسترسی مجاز نیست",
                "error.invalid_input": "ورودی نامعتبر",
                "error.connection_failed": "اتصال ناموفق",
                "error.server_error": "خطای سرور",
                "error.validation_failed": "اعتبارسنجی ناموفق",
                "error.insufficient_stock": "موجودی کافی نیست",
                "error.payment_failed": "پرداخت ناموفق",
                
                # Success Messages
                "success.saved": "با موفقیت ذخیره شد",
                "success.deleted": "با موفقیت حذف شد",
                "success.updated": "با موفقیت به‌روزرسانی شد",
                "success.created": "با موفقیت ایجاد شد",
                "success.payment_completed": "پرداخت با موفقیت انجام شد",
                "success.sync_completed": "همگام‌سازی با موفقیت انجام شد"
            }
            
            # Add all translations
            imported_count = 0
            for key, value in basic_translations.items():
                translation_data = TranslationCreate(
                    language_code=self.language_code,
                    translation_key=key,
                    translation_value=value,
                    context="Basic Dari UI translations"
                )
                
                result = await self.ml_manager.add_translation(translation_data)
                if result["success"]:
                    imported_count += 1
            
            return {
                "success": True,
                "language_code": self.language_code,
                "language_name": "Dari (دری)",
                "translations_imported": imported_count,
                "total_translations": len(basic_translations),
                "rtl_support": True,
                "message": "Dari language successfully integrated with basic translations"
            }
            
        except Exception as e:
            logger.error(f"Dari language setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_dari_product_categories(self) -> Dict[str, Any]:
        """Add common electronics categories in Dari"""
        try:
            categories_dari = {
                "electronics": "الکترونیک",
                "mobile_accessories": "لوازم جانبی موبایل",
                "computer_hardware": "سخت‌افزار کامپیوتر",
                "audio_video": "صوتی و تصویری",
                "gaming_equipment": "تجهیزات بازی",
                "networking_equipment": "تجهیزات شبکه",
                "storage_devices": "دستگاه‌های ذخیره‌سازی",
                "input_devices": "دستگاه‌های ورودی",
                "display_devices": "دستگاه‌های نمایش",
                "power_equipment": "تجهیزات برق"
            }
            
            imported_count = 0
            for key, value in categories_dari.items():
                translation_data = TranslationCreate(
                    language_code=self.language_code,
                    translation_key=f"category.{key}",
                    translation_value=value,
                    context="Electronics categories in Dari"
                )
                
                result = await self.ml_manager.add_translation(translation_data)
                if result["success"]:
                    imported_count += 1
            
            return {
                "success": True,
                "categories_added": imported_count,
                "message": "Dari product categories added successfully"
            }
            
        except Exception as e:
            logger.error(f"Dari categories setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_dari_formatting_rules(self) -> Dict[str, Any]:
        """Get Dari language formatting rules and guidelines"""
        return {
            "language_code": "prs",
            "language_name": "Dari",
            "native_name": "دری",
            "direction": "rtl",  # Right-to-left
            "script": "Arabic",
            "font_recommendations": [
                "Noto Sans Arabic",
                "Arial Unicode MS", 
                "Tahoma",
                "B Nazanin",
                "IranNastaliq"
            ],
            "number_format": {
                "decimal_separator": "٫",
                "thousands_separator": "٬",
                "currency_symbol": "؋",  # Afghan Afghani
                "currency_position": "after"  # Amount then currency
            },
            "date_format": {
                "short": "yyyy/mm/dd",
                "long": "dd MMMM yyyy",
                "calendar": "Persian/Solar Hijri"
            },
            "cultural_notes": [
                "Use formal language for business contexts",
                "Numbers can be written in Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩)",
                "Currency is Afghan Afghani (AFN)",
                "Business hours typically Sunday-Thursday",
                "Friday is the weekly holiday"
            ],
            "ui_guidelines": {
                "text_alignment": "right",
                "layout_direction": "rtl",
                "menu_position": "right_to_left",
                "form_labels": "right_aligned"
            }
        }
    
    async def validate_dari_text(self, text: str) -> Dict[str, Any]:
        """Validate Dari text for proper formatting"""
        try:
            # Basic validation for Dari text
            has_dari_chars = any('\u0600' <= char <= '\u06FF' for char in text)
            has_arabic_digits = any('\u06F0' <= char <= '\u06F9' for char in text)
            
            # Check for mixed LTR/RTL issues
            has_latin = any('a' <= char.lower() <= 'z' for char in text)
            
            return {
                "success": True,
                "is_valid_dari": has_dari_chars,
                "has_arabic_digits": has_arabic_digits,
                "has_mixed_scripts": has_dari_chars and has_latin,
                "character_count": len(text),
                "recommendations": self._get_text_recommendations(text, has_dari_chars, has_latin)
            }
            
        except Exception as e:
            logger.error(f"Dari text validation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_text_recommendations(self, text: str, has_dari: bool, has_latin: bool) -> List[str]:
        """Get recommendations for Dari text improvement"""
        recommendations = []
        
        if not has_dari:
            recommendations.append("Text does not contain Dari characters")
        
        if has_latin and has_dari:
            recommendations.append("Mixed scripts detected - consider separating or using proper RTL/LTR markers")
        
        if len(text) == 0:
            recommendations.append("Text is empty")
        
        if not recommendations:
            recommendations.append("Text formatting looks good for Dari")
        
        return recommendations

async def setup_dari_integration(db: Session) -> Dict[str, Any]:
    """Main function to setup complete Dari language integration"""
    try:
        dari_integrator = DariLanguageIntegrator(db)
        
        # Setup basic Dari language and translations
        setup_result = await dari_integrator.setup_dari_language()
        if not setup_result["success"]:
            return setup_result
        
        # Add product categories
        categories_result = await dari_integrator.add_dari_product_categories()
        
        # Get formatting rules
        formatting_rules = dari_integrator.get_dari_formatting_rules()
        
        return {
            "success": True,
            "language_setup": setup_result,
            "categories_setup": categories_result,
            "formatting_rules": formatting_rules,
            "message": "Complete Dari language integration successful"
        }
        
    except Exception as e:
        logger.error(f"Dari integration failed: {e}")
        return {"success": False, "error": str(e)}

def create_dari_integrator(db: Session) -> DariLanguageIntegrator:
    """Factory function to create Dari language integrator"""
    return DariLanguageIntegrator(db)
