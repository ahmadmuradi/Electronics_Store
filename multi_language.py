"""
Multi-Language Support Module
Handles internationalization and localization
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func, text
from pydantic import BaseModel
from enhanced_main import Base

logger = logging.getLogger(__name__)

# Database Models
class Language(Base):
    __tablename__ = "languages"
    
    language_id = Column(Integer, primary_key=True, index=True)
    code = Column(String(5), unique=True, index=True)  # e.g., 'en', 'es', 'fr'
    name = Column(String(100))  # e.g., 'English', 'Español', 'Français'
    native_name = Column(String(100))  # e.g., 'English', 'Español', 'Français'
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

class Translation(Base):
    __tablename__ = "translations"
    
    translation_id = Column(Integer, primary_key=True, index=True)
    language_id = Column(Integer, ForeignKey("languages.language_id"))
    translation_key = Column(String(200), index=True)  # e.g., 'product.name', 'ui.button.save'
    translation_value = Column(Text)
    context = Column(String(100), nullable=True)  # Additional context for translators
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    language = relationship("Language")

class ProductTranslation(Base):
    __tablename__ = "product_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    language_id = Column(Integer, ForeignKey("languages.language_id"))
    name = Column(String(200))
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product")
    language = relationship("Language")

class CategoryTranslation(Base):
    __tablename__ = "category_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    language_id = Column(Integer, ForeignKey("languages.language_id"))
    name = Column(String(200))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    category = relationship("Category")
    language = relationship("Language")

# Pydantic Models
class LanguageCreate(BaseModel):
    code: str
    name: str
    native_name: str
    is_active: bool = True

class TranslationCreate(BaseModel):
    language_code: str
    translation_key: str
    translation_value: str
    context: Optional[str] = None

class ProductTranslationCreate(BaseModel):
    product_id: int
    language_code: str
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None

class MultiLanguageManager:
    """Multi-Language Support Manager"""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_language = 'en'
        self.translations_cache = {}
        self.load_default_languages()
    
    def load_default_languages(self):
        """Load default languages if not exist"""
        try:
            default_languages = [
                {'code': 'en', 'name': 'English', 'native_name': 'English', 'is_default': True},
                {'code': 'es', 'name': 'Spanish', 'native_name': 'Español'},
                {'code': 'fr', 'name': 'French', 'native_name': 'Français'},
                {'code': 'de', 'name': 'German', 'native_name': 'Deutsch'},
                {'code': 'it', 'name': 'Italian', 'native_name': 'Italiano'},
                {'code': 'pt', 'name': 'Portuguese', 'native_name': 'Português'},
                {'code': 'ru', 'name': 'Russian', 'native_name': 'Русский'},
                {'code': 'ja', 'name': 'Japanese', 'native_name': '日本語'},
                {'code': 'ko', 'name': 'Korean', 'native_name': '한국어'},
                {'code': 'zh', 'name': 'Chinese', 'native_name': '中文'},
                {'code': 'ar', 'name': 'Arabic', 'native_name': 'العربية'},
                {'code': 'hi', 'name': 'Hindi', 'native_name': 'हिन्दी'},
                {'code': 'prs', 'name': 'Dari', 'native_name': 'دری'}
            ]
            
            for lang_data in default_languages:
                existing = self.db.query(Language).filter(Language.code == lang_data['code']).first()
                if not existing:
                    language = Language(**lang_data)
                    self.db.add(language)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to load default languages: {e}")
    
    async def add_language(self, language_data: LanguageCreate) -> Dict[str, Any]:
        """Add a new language"""
        try:
            # Check if language already exists
            existing = self.db.query(Language).filter(Language.code == language_data.code).first()
            if existing:
                return {"success": False, "error": "Language already exists"}
            
            # Create language
            language = Language(
                code=language_data.code,
                name=language_data.name,
                native_name=language_data.native_name,
                is_active=language_data.is_active
            )
            
            self.db.add(language)
            self.db.commit()
            self.db.refresh(language)
            
            return {
                "success": True,
                "language_id": language.language_id,
                "code": language.code,
                "message": f"Language {language.name} added successfully"
            }
            
        except Exception as e:
            logger.error(f"Language addition failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_languages(self, active_only: bool = True) -> Dict[str, Any]:
        """Get all languages"""
        try:
            query = self.db.query(Language)
            if active_only:
                query = query.filter(Language.is_active == True)
            
            languages = query.all()
            
            return {
                "success": True,
                "languages": [
                    {
                        "language_id": lang.language_id,
                        "code": lang.code,
                        "name": lang.name,
                        "native_name": lang.native_name,
                        "is_active": lang.is_active,
                        "is_default": lang.is_default
                    }
                    for lang in languages
                ]
            }
            
        except Exception as e:
            logger.error(f"Language retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_translation(self, translation_data: TranslationCreate) -> Dict[str, Any]:
        """Add or update a translation"""
        try:
            # Get language
            language = self.db.query(Language).filter(Language.code == translation_data.language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            # Check if translation exists
            existing = self.db.query(Translation).filter(
                Translation.language_id == language.language_id,
                Translation.translation_key == translation_data.translation_key
            ).first()
            
            if existing:
                # Update existing translation
                existing.translation_value = translation_data.translation_value
                existing.context = translation_data.context
                existing.updated_at = datetime.now()
            else:
                # Create new translation
                translation = Translation(
                    language_id=language.language_id,
                    translation_key=translation_data.translation_key,
                    translation_value=translation_data.translation_value,
                    context=translation_data.context
                )
                self.db.add(translation)
            
            self.db.commit()
            
            # Clear cache for this language
            if translation_data.language_code in self.translations_cache:
                del self.translations_cache[translation_data.language_code]
            
            return {
                "success": True,
                "message": "Translation added/updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Translation addition failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_translations(self, language_code: str, keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get translations for a language"""
        try:
            # Check cache first
            if language_code in self.translations_cache and not keys:
                return {
                    "success": True,
                    "language_code": language_code,
                    "translations": self.translations_cache[language_code]
                }
            
            # Get language
            language = self.db.query(Language).filter(Language.code == language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            # Build query
            query = self.db.query(Translation).filter(Translation.language_id == language.language_id)
            
            if keys:
                query = query.filter(Translation.translation_key.in_(keys))
            
            translations = query.all()
            
            # Convert to dictionary
            translation_dict = {
                t.translation_key: t.translation_value for t in translations
            }
            
            # Cache if getting all translations
            if not keys:
                self.translations_cache[language_code] = translation_dict
            
            return {
                "success": True,
                "language_code": language_code,
                "translations": translation_dict
            }
            
        except Exception as e:
            logger.error(f"Translation retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    def translate(self, key: str, language_code: str = None, default: str = None) -> str:
        """Get a single translation"""
        if not language_code:
            language_code = self.default_language
        
        try:
            # Check cache
            if language_code in self.translations_cache:
                return self.translations_cache[language_code].get(key, default or key)
            
            # Query database
            language = self.db.query(Language).filter(Language.code == language_code).first()
            if not language:
                return default or key
            
            translation = self.db.query(Translation).filter(
                Translation.language_id == language.language_id,
                Translation.translation_key == key
            ).first()
            
            if translation:
                return translation.translation_value
            else:
                return default or key
                
        except Exception as e:
            logger.error(f"Translation failed for key {key}: {e}")
            return default or key
    
    async def add_product_translation(self, translation_data: ProductTranslationCreate) -> Dict[str, Any]:
        """Add product translation"""
        try:
            # Get language
            language = self.db.query(Language).filter(Language.code == translation_data.language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            # Check if translation exists
            existing = self.db.query(ProductTranslation).filter(
                ProductTranslation.product_id == translation_data.product_id,
                ProductTranslation.language_id == language.language_id
            ).first()
            
            if existing:
                # Update existing
                existing.name = translation_data.name
                existing.description = translation_data.description
                existing.short_description = translation_data.short_description
                existing.updated_at = datetime.now()
            else:
                # Create new
                product_translation = ProductTranslation(
                    product_id=translation_data.product_id,
                    language_id=language.language_id,
                    name=translation_data.name,
                    description=translation_data.description,
                    short_description=translation_data.short_description
                )
                self.db.add(product_translation)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "Product translation added/updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Product translation failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def get_product_translations(self, product_id: int, language_code: str) -> Dict[str, Any]:
        """Get product translations"""
        try:
            language = self.db.query(Language).filter(Language.code == language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            translation = self.db.query(ProductTranslation).filter(
                ProductTranslation.product_id == product_id,
                ProductTranslation.language_id == language.language_id
            ).first()
            
            if translation:
                return {
                    "success": True,
                    "product_id": product_id,
                    "language_code": language_code,
                    "name": translation.name,
                    "description": translation.description,
                    "short_description": translation.short_description
                }
            else:
                return {"success": False, "error": "Translation not found"}
                
        except Exception as e:
            logger.error(f"Product translation retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_localized_products(self, language_code: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get products with translations"""
        try:
            language = self.db.query(Language).filter(Language.code == language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            # Get products with translations
            query = """
            SELECT 
                p.product_id,
                p.sku,
                p.price,
                p.stock_quantity,
                p.is_active,
                COALESCE(pt.name, p.name) as name,
                COALESCE(pt.description, p.description) as description,
                COALESCE(pt.short_description, p.description) as short_description
            FROM products p
            LEFT JOIN product_translations pt ON p.product_id = pt.product_id 
                AND pt.language_id = :language_id
            WHERE p.is_active = 1
            ORDER BY p.product_id
            LIMIT :limit OFFSET :offset
            """
            
            result = self.db.execute(text(query), {
                'language_id': language.language_id,
                'limit': limit,
                'offset': offset
            })
            
            products = [dict(row) for row in result.fetchall()]
            
            return {
                "success": True,
                "language_code": language_code,
                "products": products,
                "count": len(products)
            }
            
        except Exception as e:
            logger.error(f"Localized products retrieval failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def bulk_import_translations(self, language_code: str, translations: Dict[str, str]) -> Dict[str, Any]:
        """Bulk import translations"""
        try:
            language = self.db.query(Language).filter(Language.code == language_code).first()
            if not language:
                return {"success": False, "error": "Language not found"}
            
            imported_count = 0
            updated_count = 0
            
            for key, value in translations.items():
                existing = self.db.query(Translation).filter(
                    Translation.language_id == language.language_id,
                    Translation.translation_key == key
                ).first()
                
                if existing:
                    existing.translation_value = value
                    existing.updated_at = datetime.now()
                    updated_count += 1
                else:
                    translation = Translation(
                        language_id=language.language_id,
                        translation_key=key,
                        translation_value=value
                    )
                    self.db.add(translation)
                    imported_count += 1
            
            self.db.commit()
            
            # Clear cache
            if language_code in self.translations_cache:
                del self.translations_cache[language_code]
            
            return {
                "success": True,
                "imported_count": imported_count,
                "updated_count": updated_count,
                "total_processed": imported_count + updated_count
            }
            
        except Exception as e:
            logger.error(f"Bulk translation import failed: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def export_translations(self, language_code: str) -> Dict[str, Any]:
        """Export translations for a language"""
        try:
            result = await self.get_translations(language_code)
            if not result["success"]:
                return result
            
            return {
                "success": True,
                "language_code": language_code,
                "translations": result["translations"],
                "export_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Translation export failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_translation_progress(self) -> Dict[str, Any]:
        """Get translation progress for all languages"""
        try:
            # Get total translation keys (from default language)
            default_lang = self.db.query(Language).filter(Language.is_default == True).first()
            if not default_lang:
                default_lang = self.db.query(Language).filter(Language.code == 'en').first()
            
            if not default_lang:
                return {"success": False, "error": "No default language found"}
            
            total_keys = self.db.query(Translation).filter(
                Translation.language_id == default_lang.language_id
            ).count()
            
            # Get progress for each language
            progress_query = """
            SELECT 
                l.code,
                l.name,
                COUNT(t.translation_id) as translated_count,
                :total_keys as total_keys,
                ROUND((COUNT(t.translation_id) * 100.0 / :total_keys), 2) as progress_percent
            FROM languages l
            LEFT JOIN translations t ON l.language_id = t.language_id
            WHERE l.is_active = 1
            GROUP BY l.language_id, l.code, l.name
            ORDER BY progress_percent DESC
            """
            
            result = self.db.execute(text(progress_query), {'total_keys': total_keys})
            progress_data = [dict(row) for row in result.fetchall()]
            
            return {
                "success": True,
                "total_keys": total_keys,
                "languages": progress_data
            }
            
        except Exception as e:
            logger.error(f"Translation progress retrieval failed: {e}")
            return {"success": False, "error": str(e)}

def create_multi_language_manager(db: Session) -> MultiLanguageManager:
    """Factory function to create multi-language manager"""
    return MultiLanguageManager(db)
