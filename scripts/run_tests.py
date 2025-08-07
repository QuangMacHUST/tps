#!/usr/bin/env python3
"""
Script chạy tests cho TPS
"""

import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_patient_manager():
    """Test PatientManager functionality"""
    logger.info("Testing PatientManager...")
    
    try:
        from src.core.patient_manager import PatientManager, Patient, PatientStatus
        from datetime import datetime
        
        # Tạo temporary database
        pm = PatientManager(db_path="test_patients.db")
        
        # Test tạo patient
        test_patient = Patient(
            patient_id="TEST001",
            patient_name="Test Patient",
            birth_date=datetime(1990, 1, 1),
            sex="M",
            diagnosis="Test diagnosis",
            physician="Test Doctor",
            department="Test Department",
            status=PatientStatus.ACTIVE,
            notes="Test patient for unit testing"
        )
        
        # Test CRUD operations
        assert pm.create_patient(test_patient), "Create patient failed"
        logger.info("✓ Create patient: OK")
        
        retrieved_patient = pm.get_patient("TEST001")
        assert retrieved_patient is not None, "Get patient failed"
        assert retrieved_patient.patient_name == "Test Patient", "Patient data mismatch"
        logger.info("✓ Get patient: OK")
        
        # Test search
        patients = pm.search_patients(query="Test")
        assert len(patients) >= 1, "Search failed"
        logger.info("✓ Search patients: OK")
        
        # Test update
        test_patient.notes = "Updated notes"
        assert pm.update_patient(test_patient), "Update patient failed"
        logger.info("✓ Update patient: OK")
        
        # Test statistics
        stats = pm.get_statistics()
        assert isinstance(stats, dict), "Statistics failed"
        assert stats['total_patients'] >= 1, "Statistics data incorrect"
        logger.info("✓ Get statistics: OK")
        
        # Test backup
        assert pm.backup_database("test_backup.db"), "Backup failed"
        logger.info("✓ Backup database: OK")
        
        # Clean up
        os.remove("test_patients.db")
        if os.path.exists("test_backup.db"):
            os.remove("test_backup.db")
        
        logger.info("PatientManager tests: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"PatientManager test failed: {e}")
        return False

def test_dicom_handler():
    """Test DICOMHandler functionality"""
    logger.info("Testing DICOMHandler...")
    
    try:
        from src.core.dicom_handler import DICOMHandler
        
        handler = DICOMHandler()
        
        # Test basic functionality
        assert hasattr(handler, 'is_dicom_file'), "Missing is_dicom_file method"
        assert hasattr(handler, 'scan_directory'), "Missing scan_directory method"
        assert hasattr(handler, 'read_dicom_metadata'), "Missing read_dicom_metadata method"
        
        logger.info("✓ DICOMHandler initialization: OK")
        
        # Test with non-existent directory
        files = handler.scan_directory("nonexistent_directory")
        assert files == [], "Scan directory should return empty list for non-existent dir"
        logger.info("✓ Scan non-existent directory: OK")
        
        logger.info("DICOMHandler tests: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"DICOMHandler test failed: {e}")
        return False

def test_image_processor():
    """Test ImageProcessor functionality"""
    logger.info("Testing ImageProcessor...")
    
    try:
        from src.core.image_processor import ImageProcessor, WindowLevel
        import numpy as np
        
        processor = ImageProcessor()
        
        # Test window level
        test_array = np.random.randint(0, 1000, (100, 100))
        window = WindowLevel(center=500, width=400, name="Test")
        
        windowed = processor.apply_window_level(test_array, window)
        assert windowed.dtype == np.uint8, "Window level output should be uint8"
        assert windowed.shape == test_array.shape, "Shape should be preserved"
        logger.info("✓ Apply window/level: OK")
        
        # Test auto window level
        auto_window = processor.auto_window_level(test_array)
        assert isinstance(auto_window, WindowLevel), "Auto window should return WindowLevel"
        logger.info("✓ Auto window/level: OK")
        
        # Test image statistics
        stats = processor.get_image_statistics(test_array)
        assert 'mean' in stats, "Statistics should include mean"
        assert 'std' in stats, "Statistics should include std"
        logger.info("✓ Image statistics: OK")
        
        logger.info("ImageProcessor tests: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"ImageProcessor test failed: {e}")
        return False

def run_all_tests():
    """Chạy tất cả tests"""
    logger.info("=== CHẠY TẤT CẢ TESTS ===")
    
    tests = [
        ("PatientManager", test_patient_manager),
        ("DICOMHandler", test_dicom_handler),
        ("ImageProcessor", test_image_processor),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"{test_name}: PASSED ✓")
            else:
                failed += 1
                logger.error(f"{test_name}: FAILED ✗")
        except Exception as e:
            failed += 1
            logger.error(f"{test_name}: ERROR - {e}")
    
    logger.info(f"\n=== KẾT QUẢ TESTS ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
