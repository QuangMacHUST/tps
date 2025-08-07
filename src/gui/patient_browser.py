"""
Module Patient Browser - Giao diện duyệt và quản lý bệnh nhân

Chức năng:
- Hiển thị danh sách bệnh nhân
- Tìm kiếm và lọc bệnh nhân
- Thêm, sửa, xóa bệnh nhân
- Import DICOM data
- Export và backup
"""

import os
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QPushButton, 
    QLineEdit, QComboBox, QDateEdit, QLabel,
    QGroupBox, QSplitter, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QDialog, QFormLayout,
    QDialogButtonBox, QHeaderView, QAbstractItemView,
    QMenu, QAction, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from ..core.patient_manager import PatientManager, Patient, PatientStatus
from ..core.dicom_handler import DICOMHandler

# Cấu hình logging
logger = logging.getLogger(__name__)


class PatientEditDialog(QDialog):
    """Dialog chỉnh sửa thông tin bệnh nhân"""
    
    def __init__(self, patient: Optional[Patient] = None, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.setup_ui()
        
        if patient:
            self.load_patient_data()
        
        self.setWindowTitle("Thông tin bệnh nhân" if patient else "Thêm bệnh nhân mới")
        self.resize(400, 500)
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Patient ID
        self.patient_id_edit = QLineEdit()
        self.patient_id_edit.setMaxLength(64)
        form_layout.addRow("Mã bệnh nhân:", self.patient_id_edit)
        
        # Patient Name
        self.patient_name_edit = QLineEdit()
        self.patient_name_edit.setMaxLength(256)
        form_layout.addRow("Tên bệnh nhân:", self.patient_name_edit)
        
        # Birth Date
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(date.today())
        form_layout.addRow("Ngày sinh:", self.birth_date_edit)
        
        # Sex
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["", "M", "F", "O"])
        form_layout.addRow("Giới tính:", self.sex_combo)
        
        # Diagnosis
        self.diagnosis_edit = QTextEdit()
        self.diagnosis_edit.setMaximumHeight(80)
        form_layout.addRow("Chẩn đoán:", self.diagnosis_edit)
        
        # Physician
        self.physician_edit = QLineEdit()
        self.physician_edit.setMaxLength(256)
        form_layout.addRow("Bác sĩ:", self.physician_edit)
        
        # Department
        self.department_edit = QLineEdit()
        self.department_edit.setMaxLength(256)
        form_layout.addRow("Khoa:", self.department_edit)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in PatientStatus])
        form_layout.addRow("Trạng thái:", self.status_combo)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Ghi chú:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_patient_data(self):
        """Load dữ liệu bệnh nhân vào form"""
        if not self.patient:
            return
        
        self.patient_id_edit.setText(self.patient.patient_id)
        self.patient_id_edit.setEnabled(False)  # Không cho sửa ID
        
        self.patient_name_edit.setText(self.patient.patient_name)
        
        if self.patient.birth_date:
            self.birth_date_edit.setDate(self.patient.birth_date.date())
        
        if self.patient.sex:
            index = self.sex_combo.findText(self.patient.sex)
            if index >= 0:
                self.sex_combo.setCurrentIndex(index)
        
        self.diagnosis_edit.setPlainText(self.patient.diagnosis or "")
        self.physician_edit.setText(self.patient.physician or "")
        self.department_edit.setText(self.patient.department or "")
        
        index = self.status_combo.findText(self.patient.status.value)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        self.notes_edit.setPlainText(self.patient.notes)
    
    def get_patient_data(self) -> Dict[str, Any]:
        """Lấy dữ liệu từ form"""
        birth_date = self.birth_date_edit.date().toPyDate()
        
        return {
            'patient_id': self.patient_id_edit.text().strip(),
            'patient_name': self.patient_name_edit.text().strip(),
            'birth_date': datetime.combine(birth_date, datetime.min.time()),
            'sex': self.sex_combo.currentText() or None,
            'diagnosis': self.diagnosis_edit.toPlainText().strip() or None,
            'physician': self.physician_edit.text().strip() or None,
            'department': self.department_edit.text().strip() or None,
            'status': PatientStatus(self.status_combo.currentText()),
            'notes': self.notes_edit.toPlainText().strip()
        }


class DICOMImportWorker(QThread):
    """Worker thread cho DICOM import"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, dicom_dir: str, patient_manager: PatientManager):
        super().__init__()
        self.dicom_dir = dicom_dir
        self.patient_manager = patient_manager
        self.dicom_handler = DICOMHandler()
    
    def run(self):
        """Chạy import process"""
        try:
            self.progress.emit(0, "Đang quét DICOM files...")
            
            # Import DICOM directory
            success = self.dicom_handler.import_dicom_directory(
                self.dicom_dir, self.patient_manager
            )
            
            if success:
                self.progress.emit(100, "Import hoàn tất!")
                self.finished.emit(True, "DICOM import thành công")
            else:
                self.finished.emit(False, "DICOM import thất bại")
                
        except Exception as e:
            self.finished.emit(False, f"Lỗi import DICOM: {str(e)}")


class PatientBrowser(QWidget):
    """
    Widget duyệt và quản lý bệnh nhân
    """
    
    # Signals
    patient_selected = pyqtSignal(object)  # Patient object
    patient_double_clicked = pyqtSignal(object)
    
    def __init__(self, patient_manager: PatientManager = None):
        super().__init__()
        self.patient_manager = patient_manager or PatientManager()
        self.current_patients: List[Patient] = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_patients()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_patients)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
        logger.info("PatientBrowser được khởi tạo")
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Quản lý bệnh nhân")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Search and filter section
        search_group = QGroupBox("Tìm kiếm và lọc")
        search_layout = QGridLayout()
        
        # Search box
        search_layout.addWidget(QLabel("Tìm kiếm:"), 0, 0)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Mã BN hoặc tên bệnh nhân...")
        search_layout.addWidget(self.search_edit, 0, 1)
        
        # Status filter
        search_layout.addWidget(QLabel("Trạng thái:"), 0, 2)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tất cả", None)
        for status in PatientStatus:
            self.status_filter.addItem(status.value, status)
        search_layout.addWidget(self.status_filter, 0, 3)
        
        # Department filter
        search_layout.addWidget(QLabel("Khoa:"), 1, 0)
        self.department_filter = QComboBox()
        self.department_filter.addItem("Tất cả", None)
        search_layout.addWidget(self.department_filter, 1, 1)
        
        # Date range
        search_layout.addWidget(QLabel("Từ ngày:"), 1, 2)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(date.today().replace(day=1))  # First day of month
        search_layout.addWidget(self.date_from, 1, 3)
        
        search_layout.addWidget(QLabel("Đến ngày:"), 2, 2)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(date.today())
        search_layout.addWidget(self.date_to, 2, 3)
        
        # Search button
        self.search_btn = QPushButton("Tìm kiếm")
        search_layout.addWidget(self.search_btn, 2, 0)
        
        # Clear button
        self.clear_btn = QPushButton("Xóa bộ lọc")
        search_layout.addWidget(self.clear_btn, 2, 1)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Thêm bệnh nhân")
        self.add_btn.setIcon(QIcon("resources/icons/add.png") if Path("resources/icons/add.png").exists() else QIcon())
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("Sửa")
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Xóa")
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        self.import_btn = QPushButton("Import DICOM")
        button_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export CSV")
        button_layout.addWidget(self.export_btn)
        
        self.backup_btn = QPushButton("Backup DB")
        button_layout.addWidget(self.backup_btn)
        
        layout.addLayout(button_layout)
        
        # Patient table
        self.patient_table = QTableWidget()
        self.patient_table.setAlternatingRowColors(True)
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.patient_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Setup table columns
        columns = [
            "Mã BN", "Tên bệnh nhân", "Ngày sinh", "Giới tính",
            "Chẩn đoán", "Bác sĩ", "Khoa", "Ngày tạo", "Trạng thái"
        ]
        self.patient_table.setColumnCount(len(columns))
        self.patient_table.setHorizontalHeaderLabels(columns)
        
        # Resize columns to content
        header = self.patient_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Mã BN
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Tên BN
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Chẩn đoán
        
        layout.addWidget(self.patient_table)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Sẵn sàng")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
        
        # Context menu cho table
        self.patient_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.patient_table.customContextMenuRequested.connect(self.show_context_menu)
    
    def setup_connections(self):
        """Thiết lập kết nối signals"""
        # Search
        self.search_btn.clicked.connect(self.search_patients)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.search_edit.returnPressed.connect(self.search_patients)
        
        # Buttons
        self.add_btn.clicked.connect(self.add_patient)
        self.edit_btn.clicked.connect(self.edit_patient)
        self.delete_btn.clicked.connect(self.delete_patient)
        self.import_btn.clicked.connect(self.import_dicom)
        self.export_btn.clicked.connect(self.export_patients)
        self.backup_btn.clicked.connect(self.backup_database)
        
        # Table selection
        self.patient_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.patient_table.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def load_patients(self):
        """Load danh sách bệnh nhân"""
        try:
            self.status_label.setText("Đang tải bệnh nhân...")
            
            # Get all patients
            self.current_patients = self.patient_manager.get_all_patients()
            
            # Update table
            self.update_patient_table()
            
            # Update department filter
            self.update_department_filter()
            
            self.status_label.setText(f"Đã tải {len(self.current_patients)} bệnh nhân")
            
        except Exception as e:
            logger.error(f"Lỗi load patients: {e}")
            self.status_label.setText(f"Lỗi: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách bệnh nhân:\n{e}")
    
    def update_patient_table(self):
        """Cập nhật bảng bệnh nhân"""
        self.patient_table.setRowCount(len(self.current_patients))
        
        for row, patient in enumerate(self.current_patients):
            # Mã BN
            self.patient_table.setItem(row, 0, QTableWidgetItem(patient.patient_id))
            
            # Tên BN
            self.patient_table.setItem(row, 1, QTableWidgetItem(patient.patient_name))
            
            # Ngày sinh
            birth_date = patient.birth_date.strftime("%d/%m/%Y") if patient.birth_date else ""
            self.patient_table.setItem(row, 2, QTableWidgetItem(birth_date))
            
            # Giới tính
            self.patient_table.setItem(row, 3, QTableWidgetItem(patient.sex or ""))
            
            # Chẩn đoán
            diagnosis = (patient.diagnosis[:50] + "...") if patient.diagnosis and len(patient.diagnosis) > 50 else (patient.diagnosis or "")
            self.patient_table.setItem(row, 4, QTableWidgetItem(diagnosis))
            
            # Bác sĩ
            self.patient_table.setItem(row, 5, QTableWidgetItem(patient.physician or ""))
            
            # Khoa
            self.patient_table.setItem(row, 6, QTableWidgetItem(patient.department or ""))
            
            # Ngày tạo
            created_date = patient.created_date.strftime("%d/%m/%Y %H:%M")
            self.patient_table.setItem(row, 7, QTableWidgetItem(created_date))
            
            # Trạng thái
            status_item = QTableWidgetItem(patient.status.value)
            if patient.status == PatientStatus.ACTIVE:
                status_item.setBackground(Qt.green)
            elif patient.status == PatientStatus.INACTIVE:
                status_item.setBackground(Qt.yellow)
            elif patient.status == PatientStatus.DELETED:
                status_item.setBackground(Qt.red)
            
            self.patient_table.setItem(row, 8, status_item)
    
    def update_department_filter(self):
        """Cập nhật combo box khoa"""
        # Get unique departments
        departments = set()
        for patient in self.current_patients:
            if patient.department:
                departments.add(patient.department)
        
        # Clear and repopulate
        current_dept = self.department_filter.currentData()
        self.department_filter.clear()
        self.department_filter.addItem("Tất cả", None)
        
        for dept in sorted(departments):
            self.department_filter.addItem(dept, dept)
        
        # Restore selection
        if current_dept:
            index = self.department_filter.findData(current_dept)
            if index >= 0:
                self.department_filter.setCurrentIndex(index)
    
    def search_patients(self):
        """Tìm kiếm bệnh nhân"""
        try:
            self.status_label.setText("Đang tìm kiếm...")
            
            # Get search criteria
            query = self.search_edit.text().strip()
            status = self.status_filter.currentData()
            department = self.department_filter.currentData()
            date_from = datetime.combine(self.date_from.date().toPyDate(), datetime.min.time())
            date_to = datetime.combine(self.date_to.date().toPyDate(), datetime.max.time())
            
            # Search
            self.current_patients = self.patient_manager.search_patients(
                query=query,
                status=status,
                department=department,
                date_from=date_from,
                date_to=date_to
            )
            
            # Update table
            self.update_patient_table()
            
            self.status_label.setText(f"Tìm được {len(self.current_patients)} bệnh nhân")
            
        except Exception as e:
            logger.error(f"Lỗi search patients: {e}")
            self.status_label.setText(f"Lỗi tìm kiếm: {e}")
    
    def clear_filters(self):
        """Xóa bộ lọc"""
        self.search_edit.clear()
        self.status_filter.setCurrentIndex(0)
        self.department_filter.setCurrentIndex(0)
        self.date_from.setDate(date.today().replace(day=1))
        self.date_to.setDate(date.today())
        
        # Reload all patients
        self.load_patients()
    
    def refresh_patients(self):
        """Refresh danh sách bệnh nhân"""
        self.search_patients() if self.search_edit.text() or self.status_filter.currentIndex() > 0 else self.load_patients()
    
    def on_selection_changed(self):
        """Xử lý khi selection thay đổi"""
        selected = len(self.patient_table.selectedItems()) > 0
        self.edit_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)
        
        if selected:
            row = self.patient_table.currentRow()
            if 0 <= row < len(self.current_patients):
                patient = self.current_patients[row]
                self.patient_selected.emit(patient)
    
    def on_item_double_clicked(self):
        """Xử lý double click"""
        row = self.patient_table.currentRow()
        if 0 <= row < len(self.current_patients):
            patient = self.current_patients[row]
            self.patient_double_clicked.emit(patient)
    
    def add_patient(self):
        """Thêm bệnh nhân mới"""
        dialog = PatientEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = dialog.get_patient_data()
                
                # Validate required fields
                if not data['patient_id']:
                    QMessageBox.warning(self, "Cảnh báo", "Mã bệnh nhân không được để trống!")
                    return
                
                if not data['patient_name']:
                    QMessageBox.warning(self, "Cảnh báo", "Tên bệnh nhân không được để trống!")
                    return
                
                # Create patient
                patient = Patient(
                    patient_id=data['patient_id'],
                    patient_name=data['patient_name'],
                    birth_date=data['birth_date'],
                    sex=data['sex'],
                    diagnosis=data['diagnosis'],
                    physician=data['physician'],
                    department=data['department'],
                    status=data['status'],
                    notes=data['notes']
                )
                
                # Save to database
                if self.patient_manager.create_patient(patient):
                    QMessageBox.information(self, "Thành công", "Đã thêm bệnh nhân mới!")
                    self.load_patients()
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể thêm bệnh nhân!")
                
            except Exception as e:
                logger.error(f"Lỗi add patient: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi thêm bệnh nhân:\n{e}")
    
    def edit_patient(self):
        """Sửa thông tin bệnh nhân"""
        row = self.patient_table.currentRow()
        if row < 0 or row >= len(self.current_patients):
            return
        
        patient = self.current_patients[row]
        dialog = PatientEditDialog(patient, parent=self)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                data = dialog.get_patient_data()
                
                # Update patient object
                patient.patient_name = data['patient_name']
                patient.birth_date = data['birth_date']
                patient.sex = data['sex']
                patient.diagnosis = data['diagnosis']
                patient.physician = data['physician']
                patient.department = data['department']
                patient.status = data['status']
                patient.notes = data['notes']
                patient.modified_date = datetime.now()
                
                # Save to database
                if self.patient_manager.update_patient(patient):
                    QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin bệnh nhân!")
                    self.load_patients()
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể cập nhật bệnh nhân!")
                
            except Exception as e:
                logger.error(f"Lỗi edit patient: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật bệnh nhân:\n{e}")
    
    def delete_patient(self):
        """Xóa bệnh nhân"""
        row = self.patient_table.currentRow()
        if row < 0 or row >= len(self.current_patients):
            return
        
        patient = self.current_patients[row]
        
        reply = QMessageBox.question(
            self, 
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa bệnh nhân:\n{patient.patient_name} ({patient.patient_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.patient_manager.delete_patient(patient.patient_id):
                    QMessageBox.information(self, "Thành công", "Đã xóa bệnh nhân!")
                    self.load_patients()
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể xóa bệnh nhân!")
                    
            except Exception as e:
                logger.error(f"Lỗi delete patient: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi xóa bệnh nhân:\n{e}")
    
    def import_dicom(self):
        """Import DICOM data"""
        dicom_dir = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục DICOM",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not dicom_dir:
            return
        
        # Disable buttons
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start import worker
        self.import_worker = DICOMImportWorker(dicom_dir, self.patient_manager)
        self.import_worker.progress.connect(self.on_import_progress)
        self.import_worker.finished.connect(self.on_import_finished)
        self.import_worker.start()
    
    def on_import_progress(self, value: int, message: str):
        """Cập nhật progress import"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_import_finished(self, success: bool, message: str):
        """Hoàn tất import"""
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        if success:
            QMessageBox.information(self, "Thành công", "DICOM import hoàn tất!")
            self.load_patients()
        else:
            QMessageBox.critical(self, "Lỗi", f"DICOM import thất bại:\n{message}")
    
    def export_patients(self):
        """Export danh sách bệnh nhân ra CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export danh sách bệnh nhân",
            f"patients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV files (*.csv)"
        )
        
        if file_path:
            try:
                if self.patient_manager.export_to_csv(file_path):
                    QMessageBox.information(self, "Thành công", f"Đã export ra file:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể export file!")
                    
            except Exception as e:
                logger.error(f"Lỗi export CSV: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi export:\n{e}")
    
    def backup_database(self):
        """Backup database"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup database",
            f"backup_patients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database files (*.db)"
        )
        
        if file_path:
            try:
                if self.patient_manager.backup_database(file_path):
                    QMessageBox.information(self, "Thành công", f"Đã backup database:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể backup database!")
                    
            except Exception as e:
                logger.error(f"Lỗi backup database: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi backup:\n{e}")
    
    def show_context_menu(self, position):
        """Hiển thị context menu"""
        if self.patient_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # Actions
        edit_action = QAction("Sửa thông tin", self)
        edit_action.triggered.connect(self.edit_patient)
        menu.addAction(edit_action)
        
        delete_action = QAction("Xóa bệnh nhân", self)
        delete_action.triggered.connect(self.delete_patient)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        anonymize_action = QAction("Ẩn danh hóa", self)
        anonymize_action.triggered.connect(self.anonymize_patient)
        menu.addAction(anonymize_action)
        
        menu.exec_(self.patient_table.mapToGlobal(position))
    
    def anonymize_patient(self):
        """Ẩn danh hóa bệnh nhân"""
        row = self.patient_table.currentRow()
        if row < 0 or row >= len(self.current_patients):
            return
        
        patient = self.current_patients[row]
        
        reply = QMessageBox.question(
            self,
            "Xác nhận ẩn danh hóa",
            f"Tạo phiên bản ẩn danh cho bệnh nhân:\n{patient.patient_name} ({patient.patient_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                anon_patient = self.patient_manager.anonymize_patient(patient.patient_id)
                if anon_patient:
                    QMessageBox.information(
                        self, 
                        "Thành công", 
                        f"Đã tạo bệnh nhân ẩn danh:\n{anon_patient.patient_name} ({anon_patient.patient_id})"
                    )
                    self.load_patients()
                else:
                    QMessageBox.critical(self, "Lỗi", "Không thể ẩn danh hóa bệnh nhân!")
                    
            except Exception as e:
                logger.error(f"Lỗi anonymize patient: {e}")
                QMessageBox.critical(self, "Lỗi", f"Lỗi ẩn danh hóa:\n{e}")
    
    def get_selected_patient(self) -> Optional[Patient]:
        """Lấy bệnh nhân đang được chọn"""
        row = self.patient_table.currentRow()
        if 0 <= row < len(self.current_patients):
            return self.current_patients[row]
        return None
