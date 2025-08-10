#!/usr/bin/env python3
"""
Debug get_patient method
"""

import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core.patient_manager import PatientManager, PatientDB, PatientStudyDB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ImportError:
    from core.patient_manager import PatientManager, PatientDB, PatientStudyDB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_get_patient_method():
    """Debug get_patient method step by step"""
    try:
        pm = PatientManager()
        
        # Test get patient for SAMPLE001
        logger.info("=== Testing get_patient for SAMPLE001 ===")
        
        # Step 1: Check database directly
        engine = create_engine('sqlite:///data/patient_database/patients.db')
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            # Find patient
            db_patient = session.query(PatientDB).filter(
                PatientDB.patient_id == "SAMPLE001"
            ).first()
            
            if db_patient:
                logger.info(f"Found patient in DB: {db_patient.patient_name}")
                logger.info(f"DB Patient ID: {db_patient.id}")
                
                # Check studies relationship
                logger.info(f"Studies relationship: {db_patient.studies}")
                logger.info(f"Studies count from relationship: {len(db_patient.studies)}")
                
                # Manual query for studies
                studies = session.query(PatientStudyDB).filter(
                    PatientStudyDB.patient_db_id == db_patient.id
                ).all()
                logger.info(f"Manual studies query: {len(studies)}")
                
                for study in studies:
                    logger.info(f"  Study: {study.study_description}")
                    logger.info(f"  Study UID: {study.study_uid}")
                    logger.info(f"  File paths: {study.file_paths}")
                
            else:
                logger.error("Patient not found in database!")
        
        # Step 2: Test PatientManager get_patient
        logger.info("\n=== Testing PatientManager.get_patient ===")
        
        patient = pm.get_patient("SAMPLE001")
        if patient:
            logger.info(f"PatientManager found: {patient.patient_name}")
            logger.info(f"Studies count: {len(patient.studies)}")
            
            for i, study in enumerate(patient.studies):
                logger.info(f"  Study {i+1}: {study.study_description}")
                logger.info(f"  Study UID: {study.study_uid}")
                logger.info(f"  File paths: {study.file_paths}")
        else:
            logger.error("PatientManager could not find patient!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error debugging get_patient: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    logger.info("=== DEBUGGING GET_PATIENT METHOD ===")
    
    success = debug_get_patient_method()
    
    if success:
        logger.info("Debug completed")
    else:
        logger.error("Debug failed")

if __name__ == "__main__":
    main()
