#!/usr/bin/env python3
"""
Script khởi tạo database cho TPS
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.core.patient_manager import PatientManager, Patient, PatientStatus
except ImportError:
    # Fallback import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "patient_manager", 
        project_root / "src" / "core" / "patient_manager.py"
    )
    patient_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(patient_module)
    PatientManager = patient_module.PatientManager
    Patient = patient_module.Patient
    PatientStatus = patient_module.PatientStatus
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Khởi tạo database và tạo sample data"""
    try:
        logger.info("Khởi tạo database...")
        
        # Tạo PatientManager
        pm = PatientManager()
        
        # Tạo sample patients
        sample_patients = [
            Patient(
                patient_id="TPS001",
                patient_name="Nguyễn Văn A",
                birth_date=datetime(1980, 5, 15),
                sex="M",
                diagnosis="Ca phổi T2N0M0",
                physician="BS. Nguyễn Thị B",
                department="Xạ trị",
                status=PatientStatus.ACTIVE,
                notes="Bệnh nhân sample cho testing"
            ),
            Patient(
                patient_id="TPS002", 
                patient_name="Trần Thị C",
                birth_date=datetime(1975, 8, 22),
                sex="F",
                diagnosis="Ca vú T1N1M0",
                physician="BS. Lê Văn D",
                department="Xạ trị",
                status=PatientStatus.ACTIVE,
                notes="Bệnh nhân sample cho testing"
            ),
            Patient(
                patient_id="TPS003",
                patient_name="Phạm Văn E", 
                birth_date=datetime(1990, 12, 3),
                sex="M",
                diagnosis="Ca hạch lymphoma",
                physician="BS. Hoàng Thị F",
                department="Huyết học",
                status=PatientStatus.INACTIVE,
                notes="Bệnh nhân đã hoàn thành điều trị"
            )
        ]
        
        # Thêm sample patients
        for patient in sample_patients:
            if pm.create_patient(patient):
                logger.info(f"Đã tạo bệnh nhân: {patient.patient_name} ({patient.patient_id})")
            else:
                logger.warning(f"Không thể tạo bệnh nhân: {patient.patient_id}")
        
        # Hiển thị thống kê
        stats = pm.get_statistics()
        logger.info(f"Database đã khởi tạo với {stats['total_patients']} bệnh nhân")
        
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khởi tạo database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
