#!/usr/bin/env python3
"""
Script để force clean database và tạo lại sample data
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
    from src.core.patient_manager import PatientManager, PatientDB, PatientStudyDB, Patient, PatientStudy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime
except ImportError:
    from core.patient_manager import PatientManager, PatientDB, PatientStudyDB, Patient, PatientStudy
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_clean_database():
    """Force clean toàn bộ database"""
    try:
        # Connect trực tiếp đến database
        engine = create_engine('sqlite:///data/patient_database/patients.db')
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            # Delete all studies first (foreign key constraint)
            deleted_studies = session.query(PatientStudyDB).delete()
            logger.info(f"Deleted {deleted_studies} studies")
            
            # Delete all patients
            deleted_patients = session.query(PatientDB).delete()
            logger.info(f"Deleted {deleted_patients} patients")
            
            session.commit()
            
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning database: {e}")
        return False

def create_sample_data():
    """Tạo sample data mới"""
    try:
        pm = PatientManager()
        
        # Sample patient 1: CT + RT data
        patient1 = Patient(
            patient_id="SAMPLE001",
            patient_name="Test Patient 001^CT+RT",
            birth_date=datetime(1980, 1, 1),
            sex="M",
            diagnosis="Brain Tumor",
            physician="Dr. Test"
        )
        
        # Add sample studies với realistic data
        study1 = PatientStudy(
            study_uid="1.2.3.4.5.6.001",
            study_date=datetime(2025, 1, 1),
            study_description="Brain CT Planning",
            modality="CT",
            series_count=1,
            images_count=120,
            file_paths=[]  # Empty for now - will be populated from real DICOM
        )
        
        study2 = PatientStudy(
            study_uid="1.2.3.4.5.6.002", 
            study_date=datetime(2025, 1, 2),
            study_description="RT Treatment Plan",
            modality="RTPLAN",
            series_count=3,
            images_count=3,
            file_paths=[]  # RT Plan, RT Struct, RT Dose
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
            study_description="Brain MRI Multi-sequence",
            modality="MRI",
            series_count=4,
            images_count=480,
            file_paths=[]  # T1, T1+C, T2, FLAIR
        )
        
        patient2.add_study(study3)
        success2 = pm.create_patient(patient2)
        logger.info(f"Patient 2 created: {success2}")
        
        return success1 and success2
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False

def verify_data():
    """Verify data được tạo đúng"""
    try:
        pm = PatientManager()
        patients = pm.get_all_patients()
        
        logger.info(f"Total patients: {len(patients)}")
        
        for patient in patients:
            logger.info(f"Patient: {patient.patient_name} ({patient.patient_id})")
            logger.info(f"  Studies: {len(patient.studies)}")
            
            for i, study in enumerate(patient.studies):
                logger.info(f"    Study {i+1}: {study.study_description} ({study.modality})")
        
        patients_with_studies = [p for p in patients if p.studies]
        return len(patients_with_studies) > 0
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False

def main():
    """Main function"""
    logger.info("=== FORCE CLEAN AND CREATE SAMPLE DATA ===")
    
    # Step 1: Force clean database
    logger.info("Step 1: Force cleaning database...")
    clean_success = force_clean_database()
    
    if not clean_success:
        logger.error("Database cleanup failed!")
        return False
    
    # Step 2: Create sample data
    logger.info("Step 2: Creating sample data...")
    create_success = create_sample_data()
    
    if not create_success:
        logger.error("Sample data creation failed!")
        return False
    
    # Step 3: Verify
    logger.info("Step 3: Verifying data...")
    verify_success = verify_data()
    
    if verify_success:
        logger.info("✅ SUCCESS! Sample data created with studies.")
        return True
    else:
        logger.error("❌ FAILED! No patients with studies found.")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("Sample data created successfully!")
        print("\nNow restart the TPS application and:")
        print("1. Open Image Workspace (Ctrl+I)")
        print("2. Select 'Test Patient 001^CT+RT' or 'Test Patient 002^MRI'") 
        print("3. You should see studies in the Studies & Series tree!")
        print("4. Import real DICOM data using 'Import DICOM' button")
    else:
        print("\n❌ FAILED!")
        print("Check logs above for errors.")
    
    sys.exit(0 if success else 1)
