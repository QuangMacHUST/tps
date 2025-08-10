#!/usr/bin/env python3
"""
Test để kiểm tra database fix có hoạt động không
"""

import sys
import os
from pathlib import Path
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.patient_manager import PatientManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_patient_studies():
    """Test load patient studies từ database"""
    try:
        pm = PatientManager()
        
        # Get all patients
        patients = pm.get_all_patients()
        logger.info(f"Found {len(patients)} patients")
        
        for patient in patients:
            logger.info(f"\nPatient: {patient.patient_name} ({patient.patient_id})")
            logger.info(f"Studies: {len(patient.studies)}")
            
            for i, study in enumerate(patient.studies):
                logger.info(f"  Study {i+1}: {study.study_description}")
                logger.info(f"    UID: {study.study_uid}")
                logger.info(f"    Date: {study.study_date}")
                logger.info(f"    Modality: {study.modality}")
                logger.info(f"    Series: {study.series_count}")
                logger.info(f"    Images: {study.images_count}")
                logger.info(f"    Files: {len(study.file_paths)}")
        
        return len([p for p in patients if p.studies]) > 0
        
    except Exception as e:
        logger.error(f"Error testing patient studies: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=== TESTING DATABASE FIX ===")
    
    success = test_patient_studies()
    
    if success:
        logger.info("✅ Database fix successful! Patients have studies.")
    else:
        logger.warning("⚠️ No patients with studies found. May need to re-import DICOM data.")
    
    return success

if __name__ == "__main__":
    main()
