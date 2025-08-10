#!/usr/bin/env python3
"""
Debug script để kiểm tra tại sao studies không load được
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

def debug_database_directly():
    """Debug database directly để kiểm tra data"""
    try:
        # Connect trực tiếp đến database
        engine = create_engine('sqlite:///data/patient_database/patients.db')
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as session:
            # Check patients table
            patients = session.query(PatientDB).all()
            logger.info(f"Found {len(patients)} patients in database")
            
            for patient in patients:
                logger.info(f"Patient: {patient.patient_name} (ID: {patient.patient_id})")
                
                # Check studies for this patient
                studies = session.query(PatientStudyDB).filter(
                    PatientStudyDB.patient_db_id == patient.id
                ).all()
                
                logger.info(f"  Found {len(studies)} studies in database")
                
                for study in studies:
                    logger.info(f"    Study: {study.study_description}")
                    logger.info(f"    UID: {study.study_uid}")
                    logger.info(f"    Date: {study.study_date}")
                    logger.info(f"    Files: {study.file_paths}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error accessing database directly: {e}")
        return False

def debug_patient_manager():
    """Debug PatientManager get_patient method"""
    try:
        pm = PatientManager()
        
        # Get all patients through PatientManager
        patients = pm.get_all_patients()
        logger.info(f"PatientManager found {len(patients)} patients")
        
        for patient in patients:
            logger.info(f"Patient: {patient.patient_name}")
            logger.info(f"Studies count: {len(patient.studies)}")
            
            # Try to get individual patient
            individual_patient = pm.get_patient(patient.patient_id)
            if individual_patient:
                logger.info(f"Individual get - Studies: {len(individual_patient.studies)}")
                
                for study in individual_patient.studies:
                    logger.info(f"  Study: {study.study_description}")
            else:
                logger.error(f"Could not get individual patient: {patient.patient_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error with PatientManager: {e}")
        return False

def debug_json_parsing():
    """Debug JSON parsing issues"""
    try:
        import json
        
        # Test JSON parsing
        sample_paths = ["sample_data/ct_brain_001.dcm", "sample_data/ct_brain_002.dcm"]
        json_str = json.dumps(sample_paths)
        logger.info(f"JSON string: {json_str}")
        
        parsed_paths = json.loads(json_str)
        logger.info(f"Parsed paths: {parsed_paths}")
        
        # Test empty/None cases
        empty_json = json.dumps([])
        logger.info(f"Empty JSON: {empty_json}")
        
        parsed_empty = json.loads(empty_json)
        logger.info(f"Parsed empty: {parsed_empty}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error with JSON parsing: {e}")
        return False

def main():
    """Main debug function"""
    logger.info("=== DEBUGGING PATIENT STUDIES ===")
    
    # Debug 1: Direct database access
    logger.info("\n--- Direct Database Access ---")
    debug_database_directly()
    
    # Debug 2: PatientManager
    logger.info("\n--- PatientManager Access ---")
    debug_patient_manager()
    
    # Debug 3: JSON parsing
    logger.info("\n--- JSON Parsing ---")
    debug_json_parsing()

if __name__ == "__main__":
    main()
