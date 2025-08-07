"""
Module quản lý dữ liệu bệnh nhân

Chức năng:
- Tạo, đọc, cập nhật, xóa thông tin bệnh nhân
- Quản lý cơ sở dữ liệu bệnh nhân
- Backup và recovery dữ liệu
- Ẩn danh hóa dữ liệu bệnh nhân
"""

import os
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class PatientStatus(Enum):
    """Trạng thái của bệnh nhân trong hệ thống"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class PatientStudy:
    """Thông tin study của bệnh nhân"""
    study_uid: str
    study_date: datetime
    study_description: str
    modality: str
    series_count: int = 0
    images_count: int = 0
    file_paths: List[str] = field(default_factory=list)


@dataclass  
class Patient:
    """Thông tin bệnh nhân"""
    # Thông tin cơ bản
    patient_id: str
    patient_name: str
    birth_date: Optional[datetime] = None
    sex: Optional[str] = None
    
    # Thông tin lâm sàng
    diagnosis: Optional[str] = None
    physician: Optional[str] = None
    department: Optional[str] = None
    
    # Thông tin hệ thống
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    status: PatientStatus = PatientStatus.ACTIVE
    
    # Dữ liệu studies
    studies: List[PatientStudy] = field(default_factory=list)
    
    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Kiểm tra và validate dữ liệu sau khi tạo"""
        if not self.patient_id:
            raise ValueError("Patient ID không được để trống")
        if not self.patient_name:
            raise ValueError("Tên bệnh nhân không được để trống")
    
    def add_study(self, study: PatientStudy):
        """Thêm study mới cho bệnh nhân"""
        if not any(s.study_uid == study.study_uid for s in self.studies):
            self.studies.append(study)
            self.modified_date = datetime.now()
    
    def get_anonymized_copy(self) -> 'Patient':
        """Tạo bản sao ẩn danh của bệnh nhân"""
        anon_id = self._generate_anonymous_id()
        anon_patient = Patient(
            patient_id=anon_id,
            patient_name=f"ANON_{anon_id}",
            birth_date=None,  # Không chia sẻ ngày sinh
            sex=self.sex,
            diagnosis=self.diagnosis,
            physician="ANONYMOUS",
            department=self.department,
            created_date=self.created_date,
            modified_date=datetime.now(),
            status=self.status,
            studies=[],  # Studies sẽ cần được anonymize riêng
            notes="Anonymized patient data",
            tags=["anonymized"]
        )
        return anon_patient
    
    def _generate_anonymous_id(self) -> str:
        """Tạo ID ẩn danh dựa trên hash của dữ liệu gốc"""
        data_str = f"{self.patient_id}_{self.patient_name}_{self.birth_date}"
        return hashlib.md5(data_str.encode()).hexdigest()[:8].upper()


class PatientDB(Base):
    """Model database cho bệnh nhân"""
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(64), unique=True, nullable=False, index=True)
    patient_name = Column(String(256), nullable=False)
    birth_date = Column(DateTime, nullable=True)
    sex = Column(String(10), nullable=True)
    diagnosis = Column(Text, nullable=True)
    physician = Column(String(256), nullable=True)
    department = Column(String(256), nullable=True)
    created_date = Column(DateTime, nullable=False)
    modified_date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string
    is_anonymized = Column(Boolean, default=False)


class PatientManager:
    """
    Quản lý dữ liệu bệnh nhân
    
    Tính năng:
    - CRUD operations
    - Database management
    - Backup & Recovery
    - Data anonymization
    - Search & Filter
    """
    
    def __init__(self, db_path: Optional[str] = None, data_root: Optional[str] = None):
        """
        Khởi tạo PatientManager
        
        Args:
            db_path: Đường dẫn đến database SQLite
            data_root: Thư mục gốc chứa dữ liệu bệnh nhân
        """
        self.db_path = db_path or "data/patient_database/patients.db"
        self.data_root = Path(data_root or "data/patient_database")
        
        # Tạo thư mục nếu chưa tồn tại
        self.data_root.mkdir(parents=True, exist_ok=True)
        
        # Khởi tạo database
        self._init_database()
        
        logger.info(f"PatientManager được khởi tạo với database: {self.db_path}")
    
    def _init_database(self):
        """Khởi tạo kết nối database"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("Database đã được khởi tạo thành công")
    
    def create_patient(self, patient: Patient) -> bool:
        """
        Tạo bệnh nhân mới
        
        Args:
            patient: Thông tin bệnh nhân
            
        Returns:
            bool: True nếu thành công
        """
        try:
            with self.SessionLocal() as session:
                # Kiểm tra patient_id đã tồn tại
                existing = session.query(PatientDB).filter(
                    PatientDB.patient_id == patient.patient_id
                ).first()
                
                if existing:
                    raise ValueError(f"Patient ID {patient.patient_id} đã tồn tại")
                
                # Tạo record mới
                db_patient = PatientDB(
                    patient_id=patient.patient_id,
                    patient_name=patient.patient_name,
                    birth_date=patient.birth_date,
                    sex=patient.sex,
                    diagnosis=patient.diagnosis,
                    physician=patient.physician,
                    department=patient.department,
                    created_date=patient.created_date,
                    modified_date=patient.modified_date,
                    status=patient.status.value,
                    notes=patient.notes,
                    tags=','.join(patient.tags) if patient.tags else '',
                    is_anonymized='anonymized' in patient.tags
                )
                
                session.add(db_patient)
                session.commit()
                
                # Tạo thư mục cho bệnh nhân
                patient_dir = self.data_root / patient.patient_id
                patient_dir.mkdir(exist_ok=True)
                
                logger.info(f"Đã tạo bệnh nhân mới: {patient.patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Lỗi khi tạo bệnh nhân: {e}")
            return False
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """
        Lấy thông tin bệnh nhân theo ID
        
        Args:
            patient_id: ID bệnh nhân
            
        Returns:
            Patient hoặc None nếu không tìm thấy
        """
        try:
            with self.SessionLocal() as session:
                db_patient = session.query(PatientDB).filter(
                    PatientDB.patient_id == patient_id
                ).first()
                
                if not db_patient:
                    return None
                
                # Convert từ DB model sang Patient object
                patient = Patient(
                    patient_id=db_patient.patient_id,
                    patient_name=db_patient.patient_name,
                    birth_date=db_patient.birth_date,
                    sex=db_patient.sex,
                    diagnosis=db_patient.diagnosis,
                    physician=db_patient.physician,
                    department=db_patient.department,
                    created_date=db_patient.created_date,
                    modified_date=db_patient.modified_date,
                    status=PatientStatus(db_patient.status),
                    notes=db_patient.notes or '',
                    tags=db_patient.tags.split(',') if db_patient.tags else []
                )
                
                return patient
                
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin bệnh nhân {patient_id}: {e}")
            return None
    
    def update_patient(self, patient: Patient) -> bool:
        """
        Cập nhật thông tin bệnh nhân
        
        Args:
            patient: Thông tin bệnh nhân đã cập nhật
            
        Returns:
            bool: True nếu thành công
        """
        try:
            with self.SessionLocal() as session:
                db_patient = session.query(PatientDB).filter(
                    PatientDB.patient_id == patient.patient_id
                ).first()
                
                if not db_patient:
                    raise ValueError(f"Không tìm thấy bệnh nhân {patient.patient_id}")
                
                # Cập nhật thông tin
                db_patient.patient_name = patient.patient_name
                db_patient.birth_date = patient.birth_date
                db_patient.sex = patient.sex
                db_patient.diagnosis = patient.diagnosis
                db_patient.physician = patient.physician
                db_patient.department = patient.department
                db_patient.modified_date = datetime.now()
                db_patient.status = patient.status.value
                db_patient.notes = patient.notes
                db_patient.tags = ','.join(patient.tags) if patient.tags else ''
                
                session.commit()
                logger.info(f"Đã cập nhật bệnh nhân: {patient.patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật bệnh nhân {patient.patient_id}: {e}")
            return False
    
    def delete_patient(self, patient_id: str, permanent: bool = False) -> bool:
        """
        Xóa bệnh nhân
        
        Args:
            patient_id: ID bệnh nhân
            permanent: True để xóa vĩnh viễn, False để đánh dấu deleted
            
        Returns:
            bool: True nếu thành công
        """
        try:
            with self.SessionLocal() as session:
                db_patient = session.query(PatientDB).filter(
                    PatientDB.patient_id == patient_id
                ).first()
                
                if not db_patient:
                    raise ValueError(f"Không tìm thấy bệnh nhân {patient_id}")
                
                if permanent:
                    # Xóa thư mục dữ liệu
                    patient_dir = self.data_root / patient_id
                    if patient_dir.exists():
                        shutil.rmtree(patient_dir)
                    
                    # Xóa khỏi database
                    session.delete(db_patient)
                    logger.info(f"Đã xóa vĩnh viễn bệnh nhân: {patient_id}")
                else:
                    # Đánh dấu là deleted
                    db_patient.status = PatientStatus.DELETED.value
                    db_patient.modified_date = datetime.now()
                    logger.info(f"Đã đánh dấu xóa bệnh nhân: {patient_id}")
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Lỗi khi xóa bệnh nhân {patient_id}: {e}")
            return False
    
    def search_patients(self, 
                       query: str = "", 
                       status: Optional[PatientStatus] = None,
                       department: Optional[str] = None,
                       physician: Optional[str] = None,
                       date_from: Optional[datetime] = None,
                       date_to: Optional[datetime] = None) -> List[Patient]:
        """
        Tìm kiếm bệnh nhân với các bộ lọc
        
        Args:
            query: Từ khóa tìm kiếm (tên, ID)
            status: Trạng thái bệnh nhân
            department: Khoa
            physician: Bác sĩ
            date_from: Từ ngày
            date_to: Đến ngày
            
        Returns:
            List[Patient]: Danh sách bệnh nhân tìm được
        """
        try:
            with self.SessionLocal() as session:
                query_obj = session.query(PatientDB)
                
                # Áp dụng các filter
                if query:
                    query_obj = query_obj.filter(
                        (PatientDB.patient_id.contains(query)) |
                        (PatientDB.patient_name.contains(query))
                    )
                
                if status:
                    query_obj = query_obj.filter(PatientDB.status == status.value)
                
                if department:
                    query_obj = query_obj.filter(PatientDB.department == department)
                
                if physician:
                    query_obj = query_obj.filter(PatientDB.physician == physician)
                
                if date_from:
                    query_obj = query_obj.filter(PatientDB.created_date >= date_from)
                
                if date_to:
                    query_obj = query_obj.filter(PatientDB.created_date <= date_to)
                
                # Thực hiện query
                db_patients = query_obj.order_by(PatientDB.modified_date.desc()).all()
                
                # Convert sang Patient objects
                patients = []
                for db_patient in db_patients:
                    patient = Patient(
                        patient_id=db_patient.patient_id,
                        patient_name=db_patient.patient_name,
                        birth_date=db_patient.birth_date,
                        sex=db_patient.sex,
                        diagnosis=db_patient.diagnosis,
                        physician=db_patient.physician,
                        department=db_patient.department,
                        created_date=db_patient.created_date,
                        modified_date=db_patient.modified_date,
                        status=PatientStatus(db_patient.status),
                        notes=db_patient.notes or '',
                        tags=db_patient.tags.split(',') if db_patient.tags else []
                    )
                    patients.append(patient)
                
                logger.info(f"Tìm được {len(patients)} bệnh nhân")
                return patients
                
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm bệnh nhân: {e}")
            return []
    
    def get_all_patients(self) -> List[Patient]:
        """
        Lấy danh sách tất cả bệnh nhân (trừ deleted)
        
        Returns:
            List[Patient]: Danh sách bệnh nhân
        """
        return self.search_patients(status=PatientStatus.ACTIVE) + \
               self.search_patients(status=PatientStatus.INACTIVE) + \
               self.search_patients(status=PatientStatus.ARCHIVED)
    
    def anonymize_patient(self, patient_id: str) -> Optional[Patient]:
        """
        Tạo phiên bản ẩn danh của bệnh nhân
        
        Args:
            patient_id: ID bệnh nhân gốc
            
        Returns:
            Patient: Bệnh nhân đã ẩn danh hoặc None nếu thất bại
        """
        try:
            patient = self.get_patient(patient_id)
            if not patient:
                return None
            
            anon_patient = patient.get_anonymized_copy()
            
            # Tạo bệnh nhân ẩn danh trong database
            if self.create_patient(anon_patient):
                logger.info(f"Đã tạo bản ẩn danh cho bệnh nhân {patient_id}")
                return anon_patient
            
            return None
            
        except Exception as e:
            logger.error(f"Lỗi khi ẩn danh hóa bệnh nhân {patient_id}: {e}")
            return None
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        Sao lưu database
        
        Args:
            backup_path: Đường dẫn file backup
            
        Returns:
            bool: True nếu thành công
        """
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_patients_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Đã sao lưu database vào: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi sao lưu database: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Khôi phục database từ backup
        
        Args:
            backup_path: Đường dẫn file backup
            
        Returns:
            bool: True nếu thành công
        """
        try:
            if not Path(backup_path).exists():
                raise FileNotFoundError(f"File backup không tồn tại: {backup_path}")
            
            # Backup database hiện tại trước khi restore
            current_backup = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, current_backup)
            
            # Restore từ backup
            shutil.copy2(backup_path, self.db_path)
            
            # Khởi tạo lại connection
            self._init_database()
            
            logger.info(f"Đã khôi phục database từ: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi khôi phục database: {e}")
            return False
    
    def export_to_csv(self, file_path: str, include_deleted: bool = False) -> bool:
        """
        Xuất danh sách bệnh nhân ra file CSV
        
        Args:
            file_path: Đường dẫn file CSV
            include_deleted: Có bao gồm bệnh nhân đã xóa
            
        Returns:
            bool: True nếu thành công
        """
        try:
            patients = self.get_all_patients()
            if include_deleted:
                patients.extend(self.search_patients(status=PatientStatus.DELETED))
            
            # Tạo DataFrame
            data = []
            for patient in patients:
                data.append({
                    'Patient ID': patient.patient_id,
                    'Patient Name': patient.patient_name,
                    'Birth Date': patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else '',
                    'Sex': patient.sex or '',
                    'Diagnosis': patient.diagnosis or '',
                    'Physician': patient.physician or '',
                    'Department': patient.department or '',
                    'Created Date': patient.created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Modified Date': patient.modified_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Status': patient.status.value,
                    'Notes': patient.notes,
                    'Tags': ','.join(patient.tags)
                })
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"Đã xuất {len(patients)} bệnh nhân ra file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi xuất CSV: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Lấy thống kê về dữ liệu bệnh nhân
        
        Returns:
            Dict: Thông tin thống kê
        """
        try:
            with self.SessionLocal() as session:
                total = session.query(PatientDB).count()
                active = session.query(PatientDB).filter(PatientDB.status == PatientStatus.ACTIVE.value).count()
                inactive = session.query(PatientDB).filter(PatientDB.status == PatientStatus.INACTIVE.value).count()
                archived = session.query(PatientDB).filter(PatientDB.status == PatientStatus.ARCHIVED.value).count()
                deleted = session.query(PatientDB).filter(PatientDB.status == PatientStatus.DELETED.value).count()
                anonymized = session.query(PatientDB).filter(PatientDB.is_anonymized == True).count()
                
                # Thống kê theo department
                dept_stats = session.query(PatientDB.department, 
                                         session.query(PatientDB).filter(PatientDB.department == PatientDB.department).count()
                                         ).group_by(PatientDB.department).all()
                
                return {
                    'total_patients': total,
                    'active_patients': active,
                    'inactive_patients': inactive,
                    'archived_patients': archived,
                    'deleted_patients': deleted,
                    'anonymized_patients': anonymized,
                    'departments': dict(dept_stats) if dept_stats else {},
                    'database_file': self.db_path,
                    'data_root': str(self.data_root)
                }
                
        except Exception as e:
            logger.error(f"Lỗi khi lấy thống kê: {e}")
            return {}
