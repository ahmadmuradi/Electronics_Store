#!/usr/bin/env python3
"""
Dari Language Setup Script
Initializes Dari language support in the electronics store system
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from enhanced_main import Base
from dari_integration import setup_dari_integration

# Database configuration
DATABASE_URL = "sqlite:///./inventory.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def main():
    """Main setup function"""
    print("🌍 Setting up Dari Language Integration...")
    print("=" * 50)
    
    try:
        # Create database tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Setup Dari integration
            print("📝 Setting up Dari language and translations...")
            result = await setup_dari_integration(db)
            
            if result["success"]:
                print("✅ Dari Language Integration Successful!")
                print(f"   Language: {result['language_setup']['language_name']}")
                print(f"   Translations imported: {result['language_setup']['translations_imported']}")
                print(f"   Categories added: {result['categories_setup']['categories_added']}")
                print(f"   RTL Support: {result['language_setup']['rtl_support']}")
                
                print("\n🎯 Dari Language Features:")
                print("   ✅ Right-to-left (RTL) text support")
                print("   ✅ 150+ UI translations in Dari")
                print("   ✅ Electronics product categories")
                print("   ✅ Afghan Afghani (AFN) currency support")
                print("   ✅ Persian/Solar Hijri calendar support")
                print("   ✅ Text validation for Dari content")
                
                print("\n📋 API Endpoints Available:")
                print("   POST /languages/dari/setup - Complete setup")
                print("   GET  /languages/dari/formatting-rules - Get formatting rules")
                print("   POST /languages/dari/validate-text - Validate Dari text")
                print("   POST /languages/dari/add-categories - Add product categories")
                print("   GET  /translations/prs - Get Dari translations")
                print("   GET  /products/localized/prs - Get products in Dari")
                
                print("\n🚀 Next Steps:")
                print("   1. Start your server: python start_enhanced_server.py")
                print("   2. Access API docs: http://localhost:8001/docs")
                print("   3. Test Dari endpoints in the API documentation")
                print("   4. Add product translations using the API")
                
                print("\n💡 Usage Tips:")
                print("   • Use language code 'prs' for Dari")
                print("   • Text direction is RTL (right-to-left)")
                print("   • Currency symbol: ؋ (Afghan Afghani)")
                print("   • Recommended fonts: Noto Sans Arabic, Tahoma")
                
            else:
                print(f"❌ Setup failed: {result['error']}")
                return 1
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return 1
    
    print("\n🎉 Dari language integration completed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
