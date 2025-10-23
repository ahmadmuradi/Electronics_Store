#!/usr/bin/env python3
"""
Electronics Store Inventory System - Setup Validation Script
Validates that all components are properly configured before deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class ValidationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.issues: List[str] = []
        self.warnings_list: List[str] = []

def check_python_version() -> bool:
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        return False
    return True

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()

def check_directory_exists(dir_path: str) -> bool:
    """Check if a directory exists"""
    return Path(dir_path).is_dir()

def validate_backend() -> ValidationResult:
    """Validate backend configuration"""
    result = ValidationResult()
    base_path = Path("electronics-store-app/backend")
    
    # Check required files
    required_files = [
        "enhanced_main.py",
        "start_enhanced_server.py",
        "requirements_core.txt",
        "Dockerfile",
        ".env.example"
    ]
    
    for file in required_files:
        file_path = base_path / file
        if check_file_exists(file_path):
            result.passed += 1
            print(f"✅ {file} exists")
        else:
            result.failed += 1
            result.issues.append(f"Missing file: {file}")
            print(f"❌ {file} missing")
    
    # Check Python modules can be imported
    try:
        sys.path.insert(0, str(base_path))
        import enhanced_main
        result.passed += 1
        print("✅ Enhanced main module imports successfully")
    except ImportError as e:
        result.failed += 1
        result.issues.append(f"Import error in enhanced_main.py: {e}")
        print(f"❌ Enhanced main module import failed: {e}")
    
    return result

def validate_desktop_app() -> ValidationResult:
    """Validate desktop application"""
    result = ValidationResult()
    base_path = Path("electronics-store-app/desktop/electron-inventory-app")
    
    required_files = [
        "package.json",
        "main.js",
        "enhanced-index.html",
        "enhanced-renderer.js"
    ]
    
    for file in required_files:
        file_path = base_path / file
        if check_file_exists(file_path):
            result.passed += 1
            print(f"✅ Desktop: {file} exists")
        else:
            result.failed += 1
            result.issues.append(f"Desktop app missing: {file}")
            print(f"❌ Desktop: {file} missing")
    
    # Validate package.json
    package_json_path = base_path / "package.json"
    if check_file_exists(package_json_path):
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                if 'dependencies' in package_data and 'electron' in package_data.get('devDependencies', {}):
                    result.passed += 1
                    print("✅ Desktop: package.json is valid")
                else:
                    result.warnings += 1
                    result.warnings_list.append("Desktop package.json may be missing dependencies")
                    print("⚠️  Desktop: package.json may be incomplete")
        except json.JSONDecodeError:
            result.failed += 1
            result.issues.append("Desktop package.json is invalid JSON")
            print("❌ Desktop: package.json is invalid")
    
    return result

def validate_mobile_app() -> ValidationResult:
    """Validate mobile application"""
    result = ValidationResult()
    base_path = Path("electronics-store-app/electronics-mobile-app")
    
    required_files = [
        "package.json",
        "App.js",
        "App_Enhanced.js",
        "app.json",
        "babel.config.js"
    ]
    
    for file in required_files:
        file_path = base_path / file
        if check_file_exists(file_path):
            result.passed += 1
            print(f"✅ Mobile: {file} exists")
        else:
            result.failed += 1
            result.issues.append(f"Mobile app missing: {file}")
            print(f"❌ Mobile: {file} missing")
    
    return result

def validate_docker_setup() -> ValidationResult:
    """Validate Docker configuration"""
    result = ValidationResult()
    base_path = Path("electronics-store-app")
    
    required_files = [
        "docker-compose.yml",
        "nginx/nginx.conf",
        "monitoring/prometheus.yml",
        "database/init.sql"
    ]
    
    for file in required_files:
        file_path = base_path / file
        if check_file_exists(file_path):
            result.passed += 1
            print(f"✅ Docker: {file} exists")
        else:
            result.failed += 1
            result.issues.append(f"Docker setup missing: {file}")
            print(f"❌ Docker: {file} missing")
    
    return result

def validate_environment() -> ValidationResult:
    """Validate environment setup"""
    result = ValidationResult()
    
    # Check Python version
    if check_python_version():
        result.passed += 1
        print(f"✅ Python version: {sys.version}")
    else:
        result.failed += 1
        result.issues.append("Python 3.8+ required")
        print(f"❌ Python version too old: {sys.version}")
    
    # Check if Node.js is available (for desktop/mobile apps)
    try:
        node_version = subprocess.check_output(['node', '--version'], stderr=subprocess.DEVNULL)
        result.passed += 1
        print(f"✅ Node.js version: {node_version.decode().strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        result.warnings += 1
        result.warnings_list.append("Node.js not found - required for desktop and mobile apps")
        print("⚠️  Node.js not found")
    
    return result

def main():
    """Main validation function"""
    print("=" * 60)
    print("Electronics Store Inventory System - Setup Validation")
    print("=" * 60)
    
    total_result = ValidationResult()
    
    # Run all validations
    validations = [
        ("Environment", validate_environment),
        ("Backend API", validate_backend),
        ("Desktop App", validate_desktop_app),
        ("Mobile App", validate_mobile_app),
        ("Docker Setup", validate_docker_setup)
    ]
    
    for name, validator in validations:
        print(f"\n🔍 Validating {name}...")
        result = validator()
        total_result.passed += result.passed
        total_result.failed += result.failed
        total_result.warnings += result.warnings
        total_result.issues.extend(result.issues)
        total_result.warnings_list.extend(result.warnings_list)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {total_result.passed}")
    print(f"❌ Failed: {total_result.failed}")
    print(f"⚠️  Warnings: {total_result.warnings}")
    
    if total_result.issues:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in total_result.issues:
            print(f"  - {issue}")
    
    if total_result.warnings_list:
        print("\n⚠️  WARNINGS:")
        for warning in total_result.warnings_list:
            print(f"  - {warning}")
    
    if total_result.failed == 0:
        print("\n🎉 All critical validations passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n❌ {total_result.failed} critical issues found. Please fix before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
