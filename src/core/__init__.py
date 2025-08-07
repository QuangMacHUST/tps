"""
Module Core - Các chức năng cốt lõi của hệ thống TPS

Bao gồm:
- Quản lý dữ liệu bệnh nhân
- Xử lý DICOM I/O
- Xử lý hình ảnh y tế
- Quản lý structures/ROI
- Hình học beam
- Hệ tọa độ IEC 61217
"""

from .patient_manager import PatientManager, Patient
from .dicom_handler import DICOMHandler
from .image_processor import ImageProcessor

__all__ = [
    'PatientManager',
    'Patient', 
    'DICOMHandler',
    'ImageProcessor'
]
