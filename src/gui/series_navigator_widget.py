"""
Module Series Navigator Widget - Điều hướng DICOM Series

Chức năng:
- Hiển thị tree view của DICOM studies và series
- Thumbnail preview của series
- Load và switch giữa các series
- Series information display
- Export và import functions
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, 
    QTreeWidgetItem, QLabel, QPushButton, QFrame,
    QSplitter, QGroupBox, QGridLayout, QScrollArea,
    QProgressBar, QComboBox, QCheckBox, QLineEdit,
    QTextEdit, QTabWidget, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon

from ..core.patient_manager import PatientManager, Patient, PatientStudy
from ..core.dicom_handler import DICOMHandler, DICOMSeries, DICOMMetadata
from ..core.image_processor import ImageProcessor

# Cấu hình logging
logger = logging.getLogger(__name__)


class ThumbnailLoader(QThread):
    """Worker thread để load thumbnails"""
    
    thumbnail_ready = pyqtSignal(str, object)  # series_uid, thumbnail_pixmap
    progress_updated = pyqtSignal(int, str)  # percentage, status
    
    def __init__(self, series_list: List[DICOMSeries]):
        super().__init__()
        self.series_list = series_list
        self.image_processor = ImageProcessor()
        self._stop_flag = False
    
    def run(self):
        """Load thumbnails cho tất cả series"""
        total = len(self.series_list)
        
        for i, series in enumerate(self.series_list):
            if self._stop_flag:
                break
            
            try:
                self.progress_updated.emit(
                    int((i / total) * 100), 
                    f"Loading thumbnail {i+1}/{total}"
                )
                
                # Load middle slice để làm thumbnail
                if series.file_paths:
                    mid_index = len(series.file_paths) // 2
                    mid_file = series.file_paths[mid_index]
                    
                    # TODO: Load DICOM file và tạo thumbnail
                    # Placeholder - tạo empty pixmap
                    pixmap = QPixmap(128, 128)
                    pixmap.fill(Qt.gray)
                    
                    self.thumbnail_ready.emit(series.series_uid, pixmap)
                
            except Exception as e:
                logger.error(f"Error loading thumbnail for series {series.series_uid}: {e}")
                continue
        
        self.progress_updated.emit(100, "Thumbnails loaded")
    
    def stop(self):
        """Stop thumbnail loading"""
        self._stop_flag = True


class SeriesNavigatorWidget(QWidget):
    """
    Widget điều hướng DICOM Series
    Tương đương với series navigator trong Eclipse TPS
    """
    
    # Signals
    series_selected = pyqtSignal(object)  # DICOMSeries object
    series_loaded = pyqtSignal(object, object, object)  # image_array, spacing, origin
    patient_changed = pyqtSignal(object)  # Patient object
    
    def __init__(self, patient_manager: PatientManager = None, parent=None):
        super().__init__(parent)
        
        self.patient_manager = patient_manager or PatientManager()
        self.dicom_handler = DICOMHandler()
        self.image_processor = ImageProcessor()
        
        # Current data
        self.current_patient: Optional[Patient] = None
        self.current_studies: List[PatientStudy] = []
        self.current_series: Dict[str, DICOMSeries] = {}
        self.series_thumbnails: Dict[str, QPixmap] = {}
        
        # Thumbnail loader
        self.thumbnail_loader: Optional[ThumbnailLoader] = None
        
        self.setup_ui()
        self.load_patients()
        
        logger.info("SeriesNavigatorWidget initialized")
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Series Navigator")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh patient list")
        self.refresh_btn.clicked.connect(self.load_patients)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top: Patient selection
        patient_widget = self.create_patient_selection_widget()
        main_splitter.addWidget(patient_widget)
        
        # Middle: Studies and Series tree
        tree_widget = self.create_tree_widget()
        main_splitter.addWidget(tree_widget)
        
        # Bottom: Series details and thumbnails
        details_widget = self.create_details_widget()
        main_splitter.addWidget(details_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([100, 300, 200])
        
        layout.addWidget(main_splitter, 1)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def create_patient_selection_widget(self) -> QWidget:
        """Tạo widget chọn bệnh nhân"""
        widget = QGroupBox("Patient Selection")
        layout = QVBoxLayout()
        
        # Patient combo box
        self.patient_combo = QComboBox()
        self.patient_combo.currentTextChanged.connect(self.on_patient_changed)
        layout.addWidget(self.patient_combo)
        
        # Patient info
        self.patient_info_label = QLabel("No patient selected")
        self.patient_info_label.setWordWrap(True)
        layout.addWidget(self.patient_info_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_tree_widget(self) -> QWidget:
        """Tạo tree widget cho studies và series"""
        widget = QGroupBox("Studies & Series")
        layout = QVBoxLayout()
        
        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "Type", "Description", "Date", "Modality", "Series", "Images"
        ])
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        
        # Set column widths
        self.tree_widget.setColumnWidth(0, 80)
        self.tree_widget.setColumnWidth(1, 200)
        self.tree_widget.setColumnWidth(2, 100)
        self.tree_widget.setColumnWidth(3, 80)
        self.tree_widget.setColumnWidth(4, 60)
        self.tree_widget.setColumnWidth(5, 60)
        
        layout.addWidget(self.tree_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.load_series_btn = QPushButton("Load Series")
        self.load_series_btn.clicked.connect(self.load_selected_series)
        self.load_series_btn.setEnabled(False)
        controls_layout.addWidget(self.load_series_btn)
        
        self.import_dicom_btn = QPushButton("Import DICOM")
        self.import_dicom_btn.clicked.connect(self.import_dicom_data)
        controls_layout.addWidget(self.import_dicom_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_details_widget(self) -> QWidget:
        """Tạo widget hiển thị details và thumbnails"""
        widget = QGroupBox("Series Details")
        layout = QVBoxLayout()
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Tab 1: Series Info
        info_tab = QWidget()
        info_layout = QVBoxLayout()
        
        self.series_info_text = QTextEdit()
        self.series_info_text.setMaximumHeight(120)
        self.series_info_text.setReadOnly(True)
        info_layout.addWidget(self.series_info_text)
        
        info_tab.setLayout(info_layout)
        tab_widget.addTab(info_tab, "Information")
        
        # Tab 2: Thumbnails
        thumbnail_tab = QWidget()
        thumbnail_layout = QVBoxLayout()
        
        # Thumbnail scroll area
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Thumbnail container
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QHBoxLayout()
        self.thumbnail_container.setLayout(self.thumbnail_layout)
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        
        thumbnail_layout.addWidget(self.thumbnail_scroll)
        
        thumbnail_tab.setLayout(thumbnail_layout)
        tab_widget.addTab(thumbnail_tab, "Thumbnails")
        
        layout.addWidget(tab_widget)
        widget.setLayout(layout)
        return widget
    
    def load_patients(self):
        """Load danh sách bệnh nhân"""
        try:
            self.status_label.setText("Loading patients...")
            
            patients = self.patient_manager.get_all_patients()
            
            # Clear và repopulate combo box
            self.patient_combo.clear()
            self.patient_combo.addItem("Select Patient...", None)
            
            for patient in patients:
                display_text = f"{patient.patient_name} ({patient.patient_id})"
                self.patient_combo.addItem(display_text, patient)
            
            self.status_label.setText(f"Loaded {len(patients)} patients")
            logger.info(f"Loaded {len(patients)} patients")
            
        except Exception as e:
            logger.error(f"Error loading patients: {e}")
            self.status_label.setText(f"Error: {e}")
    
    def on_patient_changed(self):
        """Handle patient selection change"""
        patient_data = self.patient_combo.currentData()
        
        if patient_data is None:
            self.current_patient = None
            self.patient_info_label.setText("No patient selected")
            self.tree_widget.clear()
            return
        
        self.current_patient = patient_data
        
        # Update patient info
        info_text = f"""
        <b>Name:</b> {patient_data.patient_name}<br>
        <b>ID:</b> {patient_data.patient_id}<br>
        <b>Birth Date:</b> {patient_data.birth_date.strftime('%Y-%m-%d') if patient_data.birth_date else 'Unknown'}<br>
        <b>Sex:</b> {patient_data.sex or 'Unknown'}<br>
        <b>Diagnosis:</b> {patient_data.diagnosis or 'Not specified'}
        """
        self.patient_info_label.setText(info_text)
        
        # Load studies
        self.load_patient_studies()
        
        # Emit signal
        self.patient_changed.emit(patient_data)
        
        logger.info(f"Patient selected: {patient_data.patient_name}")
    
    def load_patient_studies(self):
        """Load studies cho patient hiện tại"""
        if not self.current_patient:
            return
        
        try:
            self.status_label.setText("Loading studies...")
            
            # Clear tree
            self.tree_widget.clear()
            
            # Get studies từ patient
            studies = self.current_patient.studies
            self.current_studies = studies
            
            if not studies:
                self.status_label.setText("No studies found for this patient")
                return
            
            # Add studies to tree
            for study in studies:
                study_item = QTreeWidgetItem([
                    "Study",
                    study.study_description,
                    study.study_date.strftime('%Y-%m-%d'),
                    study.modality,
                    str(study.series_count),
                    str(study.images_count)
                ])
                study_item.setData(0, Qt.UserRole, study)
                self.tree_widget.addTopLevelItem(study_item)
                
                # Load series cho study này
                self.load_study_series(study, study_item)
            
            # Expand first study
            if self.tree_widget.topLevelItemCount() > 0:
                self.tree_widget.expandItem(self.tree_widget.topLevelItem(0))
            
            self.status_label.setText(f"Loaded {len(studies)} studies")
            
        except Exception as e:
            logger.error(f"Error loading studies: {e}")
            self.status_label.setText(f"Error loading studies: {e}")
    
    def load_study_series(self, study: PatientStudy, study_item: QTreeWidgetItem):
        """Load series cho một study"""
        try:
            # Scan DICOM files từ study paths
            all_files = []
            for file_path in study.file_paths:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        all_files.extend(self.dicom_handler.scan_directory(file_path))
                    else:
                        all_files.append(file_path)
            
            if not all_files:
                logger.warning(f"No DICOM files found for study {study.study_uid}")
                return
            
            # Organize by series
            series_dict = self.dicom_handler.organize_by_series(all_files)
            
            # Add series to tree
            for series_uid, series in series_dict.items():
                series_item = QTreeWidgetItem([
                    "Series",
                    series.series_description,
                    series.series_date.strftime('%Y-%m-%d') if series.series_date else "",
                    series.modality,
                    "1",
                    str(series.slice_count)
                ])
                series_item.setData(0, Qt.UserRole, series)
                study_item.addChild(series_item)
                
                # Store series reference
                self.current_series[series_uid] = series
            
        except Exception as e:
            logger.error(f"Error loading series for study {study.study_uid}: {e}")
    
    def on_tree_selection_changed(self):
        """Handle tree selection change"""
        current_item = self.tree_widget.currentItem()
        
        if not current_item:
            self.load_series_btn.setEnabled(False)
            self.clear_series_details()
            return
        
        item_data = current_item.data(0, Qt.UserRole)
        
        if isinstance(item_data, DICOMSeries):
            # Series selected
            self.load_series_btn.setEnabled(True)
            self.show_series_details(item_data)
            self.series_selected.emit(item_data)
            
        elif isinstance(item_data, PatientStudy):
            # Study selected
            self.load_series_btn.setEnabled(False)
            self.show_study_details(item_data)
            
        else:
            self.load_series_btn.setEnabled(False)
            self.clear_series_details()
    
    def on_tree_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item double click"""
        item_data = item.data(0, Qt.UserRole)
        
        if isinstance(item_data, DICOMSeries):
            # Auto-load series on double click
            self.load_selected_series()
    
    def show_series_details(self, series: DICOMSeries):
        """Hiển thị chi tiết series"""
        try:
            # Format series information
            info_text = f"""
Series Information:
- UID: {series.series_uid}
- Description: {series.series_description}
- Modality: {series.modality}
- Series Number: {series.series_number}
- Slice Count: {series.slice_count}
- Date: {series.series_date.strftime('%Y-%m-%d %H:%M:%S') if series.series_date else 'Unknown'}
- Slice Thickness: {series.slice_thickness if series.slice_thickness else 'Unknown'} mm
- Pixel Spacing: {series.pixel_spacing if series.pixel_spacing else 'Unknown'} mm
- Files: {len(series.file_paths)}
            """
            
            self.series_info_text.setPlainText(info_text.strip())
            
            # Load thumbnail nếu chưa có
            if series.series_uid not in self.series_thumbnails:
                self.load_series_thumbnail(series)
            
        except Exception as e:
            logger.error(f"Error showing series details: {e}")
    
    def show_study_details(self, study: PatientStudy):
        """Hiển thị chi tiết study"""
        try:
            info_text = f"""
Study Information:
- UID: {study.study_uid}
- Description: {study.study_description}
- Modality: {study.modality}
- Date: {study.study_date.strftime('%Y-%m-%d %H:%M:%S')}
- Series Count: {study.series_count}
- Images Count: {study.images_count}
- Files: {len(study.file_paths)}
            """
            
            self.series_info_text.setPlainText(info_text.strip())
            
        except Exception as e:
            logger.error(f"Error showing study details: {e}")
    
    def clear_series_details(self):
        """Clear series details"""
        self.series_info_text.clear()
        self.clear_thumbnails()
    
    def load_series_thumbnail(self, series: DICOMSeries):
        """Load thumbnail cho một series"""
        try:
            if not series.file_paths:
                return
            
            # Load middle slice
            mid_index = len(series.file_paths) // 2
            mid_file = series.file_paths[mid_index]
            
            # TODO: Implement DICOM thumbnail loading
            # For now, create placeholder
            pixmap = QPixmap(128, 128)
            pixmap.fill(Qt.darkGray)
            
            self.series_thumbnails[series.series_uid] = pixmap
            self.update_thumbnail_display()
            
        except Exception as e:
            logger.error(f"Error loading thumbnail for series {series.series_uid}: {e}")
    
    def update_thumbnail_display(self):
        """Update thumbnail display"""
        # Clear existing thumbnails
        self.clear_thumbnails()
        
        # Add current thumbnails
        for series_uid, pixmap in self.series_thumbnails.items():
            thumbnail_label = QLabel()
            thumbnail_label.setPixmap(pixmap)
            thumbnail_label.setScaledContents(True)
            thumbnail_label.setFixedSize(128, 128)
            thumbnail_label.setStyleSheet("border: 1px solid gray;")
            self.thumbnail_layout.addWidget(thumbnail_label)
    
    def clear_thumbnails(self):
        """Clear thumbnail display"""
        while self.thumbnail_layout.count():
            child = self.thumbnail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def load_selected_series(self):
        """Load series được chọn"""
        current_item = self.tree_widget.currentItem()
        
        if not current_item:
            return
        
        item_data = current_item.data(0, Qt.UserRole)
        
        if not isinstance(item_data, DICOMSeries):
            return
        
        series = item_data
        
        try:
            self.status_label.setText("Loading series...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Load image data
            image_array = self.dicom_handler.load_image_series(series)
            
            if image_array is not None:
                self.progress_bar.setValue(50)
                
                # Get spacing và origin từ series
                spacing = (1.0, 1.0, 1.0)  # Default
                origin = (0.0, 0.0, 0.0)   # Default
                
                if series.slice_thickness:
                    spacing = (series.slice_thickness, 
                              series.pixel_spacing[0] if series.pixel_spacing else 1.0,
                              series.pixel_spacing[1] if series.pixel_spacing else 1.0)
                
                self.progress_bar.setValue(100)
                
                # Emit signal với loaded data
                self.series_loaded.emit(image_array, spacing, origin)
                
                self.status_label.setText(f"Series loaded: {series.series_description}")
                logger.info(f"Series loaded: {series.series_description} ({image_array.shape})")
                
            else:
                self.status_label.setText("Failed to load series")
                logger.error("Failed to load series image data")
            
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            logger.error(f"Error loading series: {e}")
            self.status_label.setText(f"Error loading series: {e}")
            self.progress_bar.setVisible(False)
    
    def import_dicom_data(self):
        """Import DICOM data từ folder"""
        from PyQt5.QtWidgets import QFileDialog
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not folder:
            return
        
        try:
            self.status_label.setText("Importing DICOM data...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Import vào patient database
            success = self.dicom_handler.import_dicom_directory(folder, self.patient_manager)
            
            self.progress_bar.setValue(100)
            
            if success:
                self.status_label.setText("DICOM import completed")
                
                # Refresh patient list
                self.load_patients()
                
                logger.info(f"DICOM import completed from: {folder}")
            else:
                self.status_label.setText("DICOM import failed")
                logger.error("DICOM import failed")
            
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            logger.error(f"Error importing DICOM data: {e}")
            self.status_label.setText(f"Import error: {e}")
            self.progress_bar.setVisible(False)
    
    def get_current_patient(self) -> Optional[Patient]:
        """Lấy patient hiện tại"""
        return self.current_patient
    
    def get_selected_series(self) -> Optional[DICOMSeries]:
        """Lấy series được chọn"""
        current_item = self.tree_widget.currentItem()
        
        if current_item:
            item_data = current_item.data(0, Qt.UserRole)
            if isinstance(item_data, DICOMSeries):
                return item_data
        
        return None
    
    def refresh_current_patient(self):
        """Refresh data cho patient hiện tại"""
        if self.current_patient:
            # Reload patient from database
            updated_patient = self.patient_manager.get_patient(self.current_patient.patient_id)
            if updated_patient:
                self.current_patient = updated_patient
                self.load_patient_studies()
