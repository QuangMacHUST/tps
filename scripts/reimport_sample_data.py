#!/usr/bin/env python3
"""
Script để re-import DICOM sample data với database schema mới
"""

import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core.patient_manager import PatientManager
    from src.core.dicom_handler import DICOMHandler
except ImportError:
    from core.patient_manager import PatientManager
    from core.dicom_handler import DICOMHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_dicom_data():
    """Tạo sample DICOM data để test"""
    try:
        pm = PatientManager()
        dicom_handler = DICOMHandler()
        
        # Tạo sample patient với studies
        from datetime import datetime
        from src.core.patient_manager import Patient, PatientStudy
        
        # Sample patient 1: CT + RT data
        patient1 = Patient(
            patient_id="SAMPLE001",
            patient_name="Test Patient 001^CT+RT",
            birth_date=datetime(1980, 1, 1),
            sex="M",
            diagnosis="Brain Tumor",
            physician="Dr. Test"
        )
        
        # Add sample studies
        study1 = PatientStudy(
            study_uid="1.2.3.4.5.6.001",
            study_date=datetime(2025, 1, 1),
            study_description="Brain CT + RT Planning",
            modality="CT",
            series_count=3,
            images_count=120,
            file_paths=[
                "sample_data/ct_brain_001.dcm",
                "sample_data/ct_brain_002.dcm"
            ]
        )
        
        study2 = PatientStudy(
            study_uid="1.2.3.4.5.6.002", 
            study_date=datetime(2025, 1, 2),
            study_description="RT Plan + Dose",
            modality="RTPLAN",
            series_count=2,
            images_count=5,
            file_paths=[
                "sample_data/rtplan_001.dcm",
                "sample_data/rtdose_001.dcm"
            ]
        )
        
        patient1.add_study(study1)
        patient1.add_study(study2)
        
        # Create patient 1
        success1 = pm.create_patient(patient1)
        logger.info(f"Patient 1 created: {success1}")
        
        # Sample patient 2: MRI data
        patient2 = Patient(
            patient_id="SAMPLE002",
            patient_name="Test Patient 002^MRI",
            birth_date=datetime(1975, 5, 15),
            sex="F",
            diagnosis="Brain Metastases",
            physician="Dr. Test"
        )
        
        study3 = PatientStudy(
            study_uid="1.2.3.4.5.6.003",
            study_date=datetime(2025, 1, 3),
            study_description="Brain MRI T1+T2",
            modality="MRI",
            series_count=4,
            images_count=200,
            file_paths=[
                "sample_data/mri_t1_001.dcm",
                "sample_data/mri_t2_001.dcm"
            ]
        )
        
        patient2.add_study(study3)
        success2 = pm.create_patient(patient2)
        logger.info(f"Patient 2 created: {success2}")
        
        return success1 and success2
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False

def clear_old_patients():
    """Clear patients without studies"""
    try:
        pm = PatientManager()
        patients = pm.get_all_patients()
        
        cleared = 0
        for patient in patients:
            if not patient.studies:
                success = pm.delete_patient(patient.patient_id)
                if success:
                    cleared += 1
                    logger.info(f"Cleared patient without studies: {patient.patient_name}")
        
        logger.info(f"Cleared {cleared} patients without studies")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing old patients: {e}")
        return False

def main():
    """Main function"""
    logger.info("=== RE-IMPORTING SAMPLE DICOM DATA ===")
    
    # Step 1: Clear old patients without studies
    logger.info("Step 1: Clearing patients without studies...")
    clear_success = clear_old_patients()
    
    # Step 2: Create new sample patients với studies
    logger.info("Step 2: Creating sample patients with studies...")
    create_success = create_sample_dicom_data()
    
    # Step 3: Verify
    logger.info("Step 3: Verifying results...")
    try:
        pm = PatientManager()
        patients = pm.get_all_patients()
        
        patients_with_studies = [p for p in patients if p.studies]
        
        logger.info(f"Total patients: {len(patients)}")
        logger.info(f"Patients with studies: {len(patients_with_studies)}")
        
        for patient in patients_with_studies:
            logger.info(f"  {patient.patient_name}: {len(patient.studies)} studies")
        
        if patients_with_studies:
            logger.info("✅ Sample data created successfully!")
            logger.info("Now restart the TPS application and test Image Workspace.")
            return True
        else:
            logger.error("❌ No patients with studies found!")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("Sample DICOM data created with studies.")
        print("Restart the TPS application and:")
        print("1. Open Image Workspace (Ctrl+I)")
        print("2. Select 'Test Patient 001^CT+RT' or 'Test Patient 002^MRI'")
        print("3. You should now see studies in the tree!")
    else:
        print("\n❌ FAILED!")
        print("Check the logs above for errors.")
    
    sys.exit(0 if success else 1)
