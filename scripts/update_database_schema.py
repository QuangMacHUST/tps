#!/usr/bin/env python3
"""
Script để update database schema cho patient studies
"""

import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try different import paths
try:
    from src.core.patient_manager import PatientManager, Base
except ImportError:
    # Try adding src directory specifically
    sys.path.insert(0, str(project_root / "src"))
    try:
        from core.patient_manager import PatientManager, Base
    except ImportError:
        # Fallback to direct path
        import importlib.util
        spec = importlib.util.spec_from_file_location("patient_manager", project_root / "src" / "core" / "patient_manager.py")
        patient_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patient_manager_module)
        PatientManager = patient_manager_module.PatientManager
        Base = patient_manager_module.Base
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """Update database schema để hỗ trợ patient studies"""
    try:
        # Tạo backup database trước khi update
        db_path = "patients.db"
        if os.path.exists(db_path):
            import shutil
            backup_path = f"patients_backup_{int(__import__('time').time())}.db"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Đã backup database: {backup_path}")
        
        # Tạo engine và update schema
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Tạo tất cả tables (sẽ tạo mới nếu chưa có)
        Base.metadata.create_all(engine)
        
        logger.info("Database schema updated successfully!")
        logger.info("Patient studies table created")
        
        # Test connection
        pm = PatientManager(db_path=db_path)
        patients = pm.get_all_patients()
        logger.info(f"Database connection OK. Found {len(patients)} patients")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
        return False

if __name__ == "__main__":
    success = update_database_schema()
    if success:
        logger.info("✅ Database schema update completed!")
        print("You can now restart the application to see patient studies.")
    else:
        logger.error("❌ Database schema update failed!")
        sys.exit(1)
