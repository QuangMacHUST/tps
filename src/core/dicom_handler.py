"""
Module xử lý DICOM I/O

Chức năng:
- Import/Export DICOM files
- Parse DICOM metadata
- Hỗ trợ các modalities: CT, MRI, PET, RT-Struct, RT-Plan, RT-Dose
- Validation và error handling
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import pydicom
from pydicom.dataset import Dataset
from pydicom import dcmread, dcmwrite
from pydicom.errors import InvalidDicomError
import numpy as np

from .patient_manager import PatientStudy

# Cấu hình logging
logger = logging.getLogger(__name__)

@dataclass
class DICOMSeries:
    """Thông tin DICOM series"""
    series_uid: str
    series_number: str
    series_description: str
    modality: str
    study_uid: str
    patient_id: str
    slice_count: int
    file_paths: List[str]
    series_date: Optional[datetime] = None
    series_time: Optional[str] = None
    slice_thickness: Optional[float] = None
    pixel_spacing: Optional[Tuple[float, float]] = None
    image_orientation: Optional[List[float]] = None
    image_position: Optional[List[float]] = None


@dataclass
class DICOMMetadata:
    """DICOM metadata tổng hợp"""
    patient_id: str
    patient_name: str
    patient_birth_date: Optional[datetime]
    patient_sex: Optional[str]
    study_uid: str
    study_date: Optional[datetime]
    study_description: str
    modality: str
    institution_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model_name: Optional[str] = None
    
    # RT-specific fields
    rt_plan_name: Optional[str] = None
    rt_plan_description: Optional[str] = None
    dose_summation_type: Optional[str] = None
    dose_type: Optional[str] = None
    dose_units: Optional[str] = None


class DICOMHandler:
    """
    Xử lý DICOM I/O operations
    
    Hỗ trợ các modality:
    - CT (Computed Tomography)
    - MRI (Magnetic Resonance Imaging) 
    - PET (Positron Emission Tomography)
    - RTIMAGE (Radiotherapy Image)
    - RTSTRUCT (RT Structure Set)
    - RTPLAN (RT Plan)
    - RTDOSE (RT Dose)
    """
    
    SUPPORTED_MODALITIES = [
        'CT', 'MRI', 'PET', 'RTIMAGE', 'RTSTRUCT', 'RTPLAN', 'RTDOSE',
        'CR', 'DX', 'MG', 'US', 'XA'  # Additional imaging modalities
    ]
    
    # RT DICOM specific modalities
    RT_MODALITIES = ['RTIMAGE', 'RTSTRUCT', 'RTPLAN', 'RTDOSE']
    
    def __init__(self):
        """Khởi tạo DICOMHandler"""
        logger.info("DICOMHandler được khởi tạo")
    
    def is_dicom_file(self, file_path: str) -> bool:
        """
        Kiểm tra xem file có phải DICOM không
        
        Args:
            file_path: Đường dẫn file
            
        Returns:
            bool: True nếu là DICOM file
        """
        try:
            pydicom.dcmread(file_path, stop_before_pixels=True)
            return True
        except (InvalidDicomError, IsADirectoryError, PermissionError):
            return False
        except Exception as e:
            logger.warning(f"Không thể đọc file {file_path}: {e}")
            return False
    
    def scan_directory(self, directory: str) -> List[str]:
        """
        Quét thư mục tìm các DICOM files
        
        Args:
            directory: Đường dẫn thư mục
            
        Returns:
            List[str]: Danh sách đường dẫn DICOM files
        """
        dicom_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.error(f"Thư mục không tồn tại: {directory}")
            return dicom_files
        
        logger.info(f"Quét thư mục DICOM: {directory}")
        
        # Quét recursively tất cả files
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                if self.is_dicom_file(str(file_path)):
                    dicom_files.append(str(file_path))
        
        logger.info(f"Tìm được {len(dicom_files)} DICOM files")
        return dicom_files
    
    def read_dicom_metadata(self, file_path: str) -> Optional[DICOMMetadata]:
        """
        Đọc metadata từ DICOM file
        
        Args:
            file_path: Đường dẫn DICOM file
            
        Returns:
            DICOMMetadata hoặc None nếu lỗi
        """
        try:
            ds = pydicom.dcmread(file_path, stop_before_pixels=True)
            
            # Parse patient info
            patient_id = getattr(ds, 'PatientID', '')
            patient_name = str(getattr(ds, 'PatientName', ''))
            
            # Parse birth date
            birth_date = None
            if hasattr(ds, 'PatientBirthDate') and ds.PatientBirthDate:
                try:
                    birth_date = datetime.strptime(ds.PatientBirthDate, '%Y%m%d')
                except ValueError:
                    pass
            
            # Parse study info
            study_uid = getattr(ds, 'StudyInstanceUID', '')
            study_description = getattr(ds, 'StudyDescription', '')
            
            # Parse study date
            study_date = None
            if hasattr(ds, 'StudyDate') and ds.StudyDate:
                try:
                    study_date = datetime.strptime(ds.StudyDate, '%Y%m%d')
                except ValueError:
                    pass
            
            # Parse modality
            modality = getattr(ds, 'Modality', '')
            
            metadata = DICOMMetadata(
                patient_id=patient_id,
                patient_name=patient_name,
                patient_birth_date=birth_date,
                patient_sex=getattr(ds, 'PatientSex', None),
                study_uid=study_uid,
                study_date=study_date,
                study_description=study_description,
                modality=modality,
                institution_name=getattr(ds, 'InstitutionName', None),
                manufacturer=getattr(ds, 'Manufacturer', None),
                model_name=getattr(ds, 'ManufacturerModelName', None)
            )
            
            # Parse RT-specific fields
            if modality == 'RTPLAN':
                metadata.rt_plan_name = getattr(ds, 'RTPlanName', None)
                metadata.rt_plan_description = getattr(ds, 'RTPlanDescription', None)
            elif modality == 'RTDOSE':
                metadata.dose_summation_type = getattr(ds, 'DoseSummationType', None)
                metadata.dose_type = getattr(ds, 'DoseType', None)
                metadata.dose_units = getattr(ds, 'DoseUnits', None)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Lỗi đọc metadata từ {file_path}: {e}")
            return None
    
    def organize_by_series(self, dicom_files: List[str]) -> Dict[str, DICOMSeries]:
        """
        Tổ chức DICOM files theo series
        
        Args:
            dicom_files: Danh sách đường dẫn DICOM files
            
        Returns:
            Dict[str, DICOMSeries]: Dictionary series_uid -> DICOMSeries
        """
        series_dict = {}
        
        logger.info(f"Tổ chức {len(dicom_files)} DICOM files theo series")
        
        for file_path in dicom_files:
            try:
                ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                
                series_uid = getattr(ds, 'SeriesInstanceUID', '')
                if not series_uid:
                    logger.warning(f"File thiếu SeriesInstanceUID: {file_path}")
                    continue
                
                if series_uid not in series_dict:
                    # Parse series date
                    series_date = None
                    if hasattr(ds, 'SeriesDate') and ds.SeriesDate:
                        try:
                            series_date = datetime.strptime(ds.SeriesDate, '%Y%m%d')
                        except ValueError:
                            pass
                    
                    # Parse pixel spacing
                    pixel_spacing = None
                    if hasattr(ds, 'PixelSpacing') and ds.PixelSpacing:
                        try:
                            pixel_spacing = (float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1]))
                        except (IndexError, ValueError):
                            pass
                    
                    # Parse slice thickness
                    slice_thickness = None
                    if hasattr(ds, 'SliceThickness'):
                        try:
                            slice_thickness = float(ds.SliceThickness)
                        except ValueError:
                            pass
                    
                    series_dict[series_uid] = DICOMSeries(
                        series_uid=series_uid,
                        series_number=str(getattr(ds, 'SeriesNumber', '')),
                        series_description=getattr(ds, 'SeriesDescription', ''),
                        modality=getattr(ds, 'Modality', ''),
                        study_uid=getattr(ds, 'StudyInstanceUID', ''),
                        patient_id=getattr(ds, 'PatientID', ''),
                        slice_count=0,
                        file_paths=[],
                        series_date=series_date,
                        series_time=getattr(ds, 'SeriesTime', None),
                        slice_thickness=slice_thickness,
                        pixel_spacing=pixel_spacing,
                        image_orientation=list(ds.ImageOrientationPatient) if hasattr(ds, 'ImageOrientationPatient') else None,
                        image_position=list(ds.ImagePositionPatient) if hasattr(ds, 'ImagePositionPatient') else None
                    )
                
                series_dict[series_uid].file_paths.append(file_path)
                series_dict[series_uid].slice_count += 1
                
            except Exception as e:
                logger.error(f"Lỗi xử lý file {file_path}: {e}")
                continue
        
        logger.info(f"Đã tổ chức thành {len(series_dict)} series")
        return series_dict
    
    def load_image_series(self, series: DICOMSeries) -> Optional[np.ndarray]:
        """
        Load image data từ DICOM series
        
        Args:
            series: DICOMSeries object
            
        Returns:
            np.ndarray: Image data (3D array) hoặc None nếu lỗi
        """
        if not series.file_paths:
            logger.error("Series không có file nào")
            return None
        
        try:
            logger.info(f"Loading image series: {series.series_description} ({series.slice_count} slices)")
            
            # Sort files theo ImagePositionPatient nếu có
            sorted_files = self._sort_dicom_files(series.file_paths)
            
            # Load first slice để lấy thông tin
            first_ds = pydicom.dcmread(sorted_files[0])
            
            if not hasattr(first_ds, 'pixel_array'):
                logger.error("DICOM không chứa image data")
                return None
            
            # Khởi tạo array 3D
            first_slice = first_ds.pixel_array
            image_shape = (len(sorted_files), first_slice.shape[0], first_slice.shape[1])
            image_array = np.zeros(image_shape, dtype=first_slice.dtype)
            
            # Load tất cả slices
            for i, file_path in enumerate(sorted_files):
                ds = pydicom.dcmread(file_path)
                image_array[i] = ds.pixel_array
            
            logger.info(f"Đã load image array shape: {image_array.shape}")
            return image_array
            
        except Exception as e:
            logger.error(f"Lỗi load image series: {e}")
            return None
    
    def _sort_dicom_files(self, file_paths: List[str]) -> List[str]:
        """
        Sắp xếp DICOM files theo thứ tự slice position
        
        Args:
            file_paths: Danh sách đường dẫn files
            
        Returns:
            List[str]: Files đã được sắp xếp
        """
        files_with_pos = []
        
        for file_path in file_paths:
            try:
                ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                
                # Ưu tiên ImagePositionPatient[2] (Z coordinate)
                if hasattr(ds, 'ImagePositionPatient') and len(ds.ImagePositionPatient) >= 3:
                    z_pos = float(ds.ImagePositionPatient[2])
                # Fallback về InstanceNumber
                elif hasattr(ds, 'InstanceNumber'):
                    z_pos = float(ds.InstanceNumber)
                # Fallback về SliceLocation
                elif hasattr(ds, 'SliceLocation'):
                    z_pos = float(ds.SliceLocation)
                else:
                    z_pos = 0
                
                files_with_pos.append((z_pos, file_path))
                
            except Exception as e:
                logger.warning(f"Không thể xác định vị trí slice cho {file_path}: {e}")
                files_with_pos.append((0, file_path))
        
        # Sort theo z position
        files_with_pos.sort(key=lambda x: x[0])
        
        return [file_path for _, file_path in files_with_pos]
    
    def export_dicom(self, output_dir: str, dataset: Dataset, filename: str = None) -> bool:
        """
        Export DICOM dataset ra file
        
        Args:
            output_dir: Thư mục output
            dataset: DICOM dataset
            filename: Tên file (optional)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not filename:
                # Tạo filename từ SOP Instance UID
                sop_uid = getattr(dataset, 'SOPInstanceUID', 'unknown')
                filename = f"{sop_uid}.dcm"
            
            file_path = output_path / filename
            
            # Write DICOM file
            dcmwrite(str(file_path), dataset)
            
            logger.info(f"Đã export DICOM: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi export DICOM: {e}")
            return False
    
    def anonymize_dicom(self, input_path: str, output_path: str, 
                       patient_id: str = "ANON", patient_name: str = "ANONYMOUS") -> bool:
        """
        Ẩn danh hóa DICOM file
        
        Args:
            input_path: Đường dẫn file input
            output_path: Đường dẫn file output
            patient_id: Patient ID mới
            patient_name: Patient name mới
            
        Returns:
            bool: True nếu thành công
        """
        try:
            ds = pydicom.dcmread(input_path)
            
            # Các fields cần anonymize
            anonymize_fields = {
                'PatientID': patient_id,
                'PatientName': patient_name,
                'PatientBirthDate': '',
                'PatientSex': '',
                'PatientAge': '',
                'PatientWeight': '',
                'PatientSize': '',
                'PatientAddress': '',
                'PatientTelephoneNumbers': '',
                'InstitutionName': 'ANONYMOUS',
                'InstitutionAddress': '',
                'ReferringPhysicianName': 'ANONYMOUS',
                'PerformingPhysicianName': 'ANONYMOUS',
                'OperatorsName': 'ANONYMOUS',
                'StudyID': 'ANON_STUDY',
                'AccessionNumber': '',
            }
            
            # Apply anonymization
            for field, value in anonymize_fields.items():
                if hasattr(ds, field):
                    setattr(ds, field, value)
            
            # Tạo thư mục output nếu cần
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write anonymized file
            dcmwrite(output_path, ds)
            
            logger.info(f"Đã anonymize DICOM: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi anonymize DICOM: {e}")
            return False
    
    def validate_dicom_integrity(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Validate tính toàn vẹn của DICOM files
        
        Args:
            file_paths: Danh sách đường dẫn files
            
        Returns:
            Dict: {
                'valid': [list of valid files],
                'invalid': [list of invalid files],
                'errors': [list of error messages]
            }
        """
        result = {
            'valid': [],
            'invalid': [],
            'errors': []
        }
        
        logger.info(f"Validate {len(file_paths)} DICOM files")
        
        for file_path in file_paths:
            try:
                ds = pydicom.dcmread(file_path)
                
                # Basic validation checks
                required_fields = ['PatientID', 'StudyInstanceUID', 'SeriesInstanceUID', 'SOPInstanceUID']
                missing_fields = []
                
                for field in required_fields:
                    if not hasattr(ds, field) or not getattr(ds, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    error_msg = f"{file_path}: Missing required fields: {missing_fields}"
                    result['errors'].append(error_msg)
                    result['invalid'].append(file_path)
                else:
                    result['valid'].append(file_path)
                
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                result['errors'].append(error_msg)
                result['invalid'].append(file_path)
        
        logger.info(f"Validation complete: {len(result['valid'])} valid, {len(result['invalid'])} invalid")
        return result
    
    def convert_to_patient_studies(self, series_dict: Dict[str, DICOMSeries]) -> List[PatientStudy]:
        """
        Convert DICOM series thành PatientStudy objects
        
        Args:
            series_dict: Dictionary of DICOM series
            
        Returns:
            List[PatientStudy]: Danh sách studies
        """
        studies_dict = {}
        
        # Group series by study
        for series in series_dict.values():
            study_uid = series.study_uid
            if study_uid not in studies_dict:
                studies_dict[study_uid] = {
                    'series': [],
                    'modalities': set(),
                    'total_images': 0
                }
            
            studies_dict[study_uid]['series'].append(series)
            studies_dict[study_uid]['modalities'].add(series.modality)
            studies_dict[study_uid]['total_images'] += series.slice_count
        
        # Convert to PatientStudy objects
        patient_studies = []
        for study_uid, study_data in studies_dict.items():
            # Lấy thông tin từ series đầu tiên
            first_series = study_data['series'][0]
            
            # Determine study description
            modalities_str = '+'.join(sorted(study_data['modalities']))
            study_desc = f"{modalities_str} Study"
            
            # Determine study date (từ series date)
            study_date = first_series.series_date or datetime.now()
            
            # Collect tất cả file paths
            all_file_paths = []
            for series in study_data['series']:
                all_file_paths.extend(series.file_paths)
            
            patient_study = PatientStudy(
                study_uid=study_uid,
                study_date=study_date,
                study_description=study_desc,
                modality=modalities_str,
                series_count=len(study_data['series']),
                images_count=study_data['total_images'],
                file_paths=all_file_paths
            )
            
            patient_studies.append(patient_study)
        
        logger.info(f"Converted {len(patient_studies)} studies từ {len(series_dict)} series")
        return patient_studies
    
    def import_dicom_directory(self, directory: str, patient_manager) -> bool:
        """
        Import toàn bộ DICOM directory vào patient database
        
        Args:
            directory: Đường dẫn thư mục DICOM
            patient_manager: PatientManager instance
            
        Returns:
            bool: True nếu thành công
        """
        try:
            logger.info(f"Import DICOM directory: {directory}")
            
            # Quét tìm DICOM files
            dicom_files = self.scan_directory(directory)
            if not dicom_files:
                logger.warning("Không tìm thấy DICOM files nào")
                return False
            
            # Validate files
            validation = self.validate_dicom_integrity(dicom_files)
            if validation['invalid']:
                logger.warning(f"Có {len(validation['invalid'])} files không hợp lệ")
                for error in validation['errors']:
                    logger.warning(error)
            
            # Organize by series
            series_dict = self.organize_by_series(validation['valid'])
            if not series_dict:
                logger.error("Không thể organize DICOM series")
                return False
            
            # Group by patient
            patients_dict = {}
            for series in series_dict.values():
                patient_id = series.patient_id
                if patient_id not in patients_dict:
                    patients_dict[patient_id] = []
                patients_dict[patient_id].append(series)
            
            # Import từng patient
            success_count = 0
            for patient_id, patient_series in patients_dict.items():
                try:
                    # Lấy metadata từ series đầu tiên
                    first_file = patient_series[0].file_paths[0]
                    metadata = self.read_dicom_metadata(first_file)
                    
                    if not metadata:
                        logger.error(f"Không thể đọc metadata cho patient {patient_id}")
                        continue
                    
                    # Tạo hoặc cập nhật patient
                    from .patient_manager import Patient, PatientStatus
                    
                    existing_patient = patient_manager.get_patient(patient_id)
                    if existing_patient:
                        patient = existing_patient
                        logger.info(f"Cập nhật patient hiện có: {patient_id}")
                    else:
                        patient = Patient(
                            patient_id=metadata.patient_id,
                            patient_name=metadata.patient_name,
                            birth_date=metadata.patient_birth_date,
                            sex=metadata.patient_sex,
                            created_date=datetime.now(),
                            status=PatientStatus.ACTIVE
                        )
                        logger.info(f"Tạo patient mới: {patient_id}")
                    
                    # Convert series to studies
                    series_dict_for_patient = {s.series_uid: s for s in patient_series}
                    studies = self.convert_to_patient_studies(series_dict_for_patient)
                    
                    # Add studies to patient
                    for study in studies:
                        patient.add_study(study)
                    
                    # Save patient
                    if existing_patient:
                        patient_manager.update_patient(patient)
                    else:
                        patient_manager.create_patient(patient)
                    
                    success_count += 1
                    logger.info(f"Đã import patient {patient_id} với {len(studies)} studies")
                    
                except Exception as e:
                    logger.error(f"Lỗi import patient {patient_id}: {e}")
                    continue
            
            logger.info(f"Import hoàn tất: {success_count}/{len(patients_dict)} patients thành công")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Lỗi import DICOM directory: {e}")
            return False
