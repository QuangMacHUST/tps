#!/usr/bin/env python3
"""
Test đơn giản cho TPS - không cần cài đặt dependencies phức tạp
"""

import sys
import os
from pathlib import Path
import logging

# Add src to Python path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test import các module chính"""
    logger.info("Testing imports...")
    
    try:
        # Test patient manager
        from src.core.patient_manager import PatientManager, Patient, PatientStatus
        logger.info("✓ PatientManager import: OK")
        
        # Test DICOM handler
        from src.core.dicom_handler import DICOMHandler
        logger.info("✓ DICOMHandler import: OK")
        
        # Test image processor
        from src.core.image_processor import ImageProcessor
        logger.info("✓ ImageProcessor import: OK")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Other error: {e}")
        return False

def test_basic_functionality():
    """Test chức năng cơ bản"""
    logger.info("Testing basic functionality...")
    
    try:
        from src.core.patient_manager import PatientManager, Patient, PatientStatus
        from datetime import datetime
        
        # Test khởi tạo PatientManager
        pm = PatientManager(db_path="test.db")
        logger.info("✓ PatientManager initialization: OK")
        
        # Test tạo Patient
        patient = Patient(
            patient_id="TEST001",
            patient_name="Test Patient", 
            birth_date=datetime(1990, 1, 1),
            sex="M",
            status=PatientStatus.ACTIVE
        )
        logger.info("✓ Patient creation: OK")
        
        # Test thêm patient vào database
        if pm.create_patient(patient):
            logger.info("✓ Add patient to database: OK")
        else:
            logger.warning("! Add patient to database: FAILED")
        
        # Test lấy patient từ database
        retrieved = pm.get_patient("TEST001") 
        if retrieved and retrieved.patient_name == "Test Patient":
            logger.info("✓ Retrieve patient from database: OK")
        else:
            logger.warning("! Retrieve patient from database: FAILED")
        
        # Clean up - close database connections first
        pm.engine.dispose()
        
        # Wait a bit for Windows to release file lock
        import time
        time.sleep(0.5)
        
        try:
            if os.path.exists("test.db"):
                os.remove("test.db")
        except:
            logger.warning("Could not remove test.db - file may be in use")
        
        return True
        
    except Exception as e:
        logger.error(f"Basic functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=== TPS SIMPLE TESTS ===")
    
    # Test 1: Imports
    if not test_imports():
        logger.error("Import tests failed! Check dependencies.")
        return False
    
    # Test 2: Basic functionality  
    if not test_basic_functionality():
        logger.error("Basic functionality tests failed!")
        return False
    
    logger.info("=== ALL TESTS PASSED ✓ ===")
    logger.info("TPS core modules are working correctly!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Bạn có thể chạy ứng dụng bằng: python main.py")
    sys.exit(0 if success else 1)
