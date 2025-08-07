"""
Module Main Window - Cửa sổ chính của ứng dụng TPS

Chức năng:
- Layout chính của ứng dụng
- Menu bar và toolbar
- Status bar
- Quản lý các widget con
- Settings và preferences
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QMenuBar, QMenu, QAction,
    QToolBar, QStatusBar, QLabel, QMessageBox,
    QApplication, QFileDialog, QDialog
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QKeySequence

from ..core.patient_manager import PatientManager
from .patient_browser import PatientBrowser

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tps.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AboutDialog(QDialog):
    """Dialog About"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Về TPS")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Logo (nếu có)
        logo_label = QLabel()
        if Path("resources/icons/logo.png").exists():
            pixmap = QPixmap("resources/icons/logo.png")
            logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("Hệ Thống Lập Kế Hoạch Xạ Trị (TPS)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Version
        version_label = QLabel("Phiên bản: 0.1.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # Description
        desc_label = QLabel(
            "Hệ thống lập kế hoạch xạ trị toàn diện với đầy đủ các tính năng:\n"
            "• Quản lý dữ liệu bệnh nhân\n"
            "• Import/Export DICOM\n"
            "• Contouring và Planning\n"
            "• Dose Calculation và Optimization\n"
            "• Visualization và QA"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Copyright
        copyright_label = QLabel("© 2024 TPS Development Team")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng TPS
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("TPS", "TreatmentPlanningSystem")
        
        # Initialize patient manager
        self.patient_manager = PatientManager()
        
        # Setup UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_connections()
        
        # Restore window state
        self.restore_settings()
        
        # Auto-save settings timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_settings)
        self.save_timer.start(30000)  # Save every 30 seconds
        
        logger.info("MainWindow được khởi tạo thành công")
    
    def setup_ui(self):
        """Thiết lập giao diện chính"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Patient Browser
        self.patient_browser = PatientBrowser(self.patient_manager)
        self.patient_browser.setMinimumWidth(600)
        main_splitter.addWidget(self.patient_browser)
        
        # Right panel - Tab widget cho các modules khác
        self.right_tabs = QTabWidget()
        self.right_tabs.setMinimumWidth(400)
        
        # Placeholder tabs (sẽ được thay thế bằng modules thực)
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout()
        
        welcome_label = QLabel("Chào mừng đến với TPS!")
        welcome_font = QFont()
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        info_label = QLabel(
            "Hệ thống lập kế hoạch xạ trị toàn diện\n\n"
            "Các tính năng hiện có:\n"
            "✓ Quản lý dữ liệu bệnh nhân\n"
            "✓ Import/Export DICOM\n"
            "✓ Database management\n"
            "✓ Search và filter\n\n"
            "Đang phát triển:\n"
            "• Image Viewer\n"
            "• Contouring Tools\n"
            "• Planning Workspace\n"
            "• Dose Calculation\n"
            "• Optimization"
        )
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        welcome_layout.addWidget(info_label)
        
        welcome_widget.setLayout(welcome_layout)
        self.right_tabs.addTab(welcome_widget, "Tổng quan")
        
        # Statistics tab
        stats_widget = self.create_statistics_widget()
        self.right_tabs.addTab(stats_widget, "Thống kê")
        
        main_splitter.addWidget(self.right_tabs)
        
        # Set splitter proportions
        main_splitter.setSizes([700, 500])
        
        # Window properties
        self.setWindowTitle("TPS - Treatment Planning System")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Set window icon (nếu có)
        if Path("resources/icons/tps.ico").exists():
            self.setWindowIcon(QIcon("resources/icons/tps.ico"))
    
    def create_statistics_widget(self) -> QWidget:
        """Tạo widget thống kê"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Thống kê hệ thống")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Statistics content
        self.stats_label = QLabel("Đang tải thống kê...")
        self.stats_label.setWordWrap(True)
        self.stats_label.setAlignment(Qt.AlignTop)
        layout.addWidget(self.stats_label)
        
        # Refresh button
        from PyQt5.QtWidgets import QPushButton
        refresh_btn = QPushButton("Cập nhật thống kê")
        refresh_btn.clicked.connect(self.update_statistics)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        # Load initial statistics
        QTimer.singleShot(1000, self.update_statistics)  # Delay để patient manager khởi tạo
        
        return widget
    
    def setup_menu_bar(self):
        """Thiết lập menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # New Patient
        new_patient_action = QAction("&New Patient", self)
        new_patient_action.setShortcut(QKeySequence.New)
        new_patient_action.setStatusTip("Thêm bệnh nhân mới")
        new_patient_action.triggered.connect(self.patient_browser.add_patient)
        file_menu.addAction(new_patient_action)
        
        # Import DICOM
        import_action = QAction("&Import DICOM", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import DICOM data")
        import_action.triggered.connect(self.patient_browser.import_dicom)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Export
        export_action = QAction("&Export CSV", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export danh sách bệnh nhân")
        export_action.triggered.connect(self.patient_browser.export_patients)
        file_menu.addAction(export_action)
        
        # Backup
        backup_action = QAction("&Backup Database", self)
        backup_action.setShortcut("Ctrl+B")
        backup_action.setStatusTip("Backup database")
        backup_action.triggered.connect(self.patient_browser.backup_database)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("Thoát ứng dụng")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Find
        find_action = QAction("&Find", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.setStatusTip("Tìm kiếm bệnh nhân")
        find_action.triggered.connect(self.focus_search)
        edit_menu.addAction(find_action)
        
        # Refresh
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.setStatusTip("Refresh danh sách")
        refresh_action.triggered.connect(self.patient_browser.refresh_patients)
        edit_menu.addAction(refresh_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Show Statistics
        stats_action = QAction("&Statistics", self)
        stats_action.setStatusTip("Hiển thị thống kê")
        stats_action.triggered.connect(lambda: self.right_tabs.setCurrentIndex(1))
        view_menu.addAction(stats_action)
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Settings
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Cài đặt ứng dụng")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # About
        about_action = QAction("&About TPS", self)
        about_action.setStatusTip("Về TPS")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # About Qt
        about_qt_action = QAction("About &Qt", self)
        about_qt_action.setStatusTip("Về Qt")
        about_qt_action.triggered.connect(QApplication.aboutQt)
        help_menu.addAction(about_qt_action)
    
    def setup_toolbar(self):
        """Thiết lập toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # New Patient
        new_action = QAction("New", self)
        new_action.setStatusTip("Thêm bệnh nhân mới")
        new_action.triggered.connect(self.patient_browser.add_patient)
        toolbar.addAction(new_action)
        
        # Import DICOM
        import_action = QAction("Import", self)
        import_action.setStatusTip("Import DICOM")
        import_action.triggered.connect(self.patient_browser.import_dicom)
        toolbar.addAction(import_action)
        
        # Export
        export_action = QAction("Export", self)
        export_action.setStatusTip("Export CSV")
        export_action.triggered.connect(self.patient_browser.export_patients)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Refresh
        refresh_action = QAction("Refresh", self)
        refresh_action.setStatusTip("Refresh danh sách")
        refresh_action.triggered.connect(self.patient_browser.refresh_patients)
        toolbar.addAction(refresh_action)
    
    def setup_status_bar(self):
        """Thiết lập status bar"""
        self.status_bar = self.statusBar()
        
        # Main status
        self.status_label = QLabel("Sẵn sàng")
        self.status_bar.addWidget(self.status_label)
        
        # Patient count
        self.patient_count_label = QLabel()
        self.status_bar.addPermanentWidget(self.patient_count_label)
        
        # Database status
        self.db_status_label = QLabel(f"DB: {self.patient_manager.db_path}")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        # Update patient count
        self.update_patient_count()
    
    def setup_connections(self):
        """Thiết lập kết nối signals"""
        # Patient browser signals
        self.patient_browser.patient_selected.connect(self.on_patient_selected)
        self.patient_browser.patient_double_clicked.connect(self.on_patient_double_clicked)
    
    def focus_search(self):
        """Focus vào search box"""
        self.patient_browser.search_edit.setFocus()
        self.patient_browser.search_edit.selectAll()
    
    def update_patient_count(self):
        """Cập nhật số lượng bệnh nhân trong status bar"""
        try:
            count = len(self.patient_browser.current_patients)
            self.patient_count_label.setText(f"Patients: {count}")
        except Exception as e:
            logger.warning(f"Không thể cập nhật patient count: {e}")
    
    def update_statistics(self):
        """Cập nhật thống kê"""
        try:
            stats = self.patient_manager.get_statistics()
            
            stats_text = f"""
<h3>Thống kê bệnh nhân:</h3>
<table>
<tr><td><b>Tổng số bệnh nhân:</b></td><td>{stats.get('total_patients', 0)}</td></tr>
<tr><td><b>Đang hoạt động:</b></td><td>{stats.get('active_patients', 0)}</td></tr>
<tr><td><b>Không hoạt động:</b></td><td>{stats.get('inactive_patients', 0)}</td></tr>
<tr><td><b>Đã lưu trữ:</b></td><td>{stats.get('archived_patients', 0)}</td></tr>
<tr><td><b>Đã xóa:</b></td><td>{stats.get('deleted_patients', 0)}</td></tr>
<tr><td><b>Đã ẩn danh:</b></td><td>{stats.get('anonymized_patients', 0)}</td></tr>
</table>

<h3>Theo khoa:</h3>
<table>
"""
            
            departments = stats.get('departments', {})
            if departments:
                for dept, count in departments.items():
                    dept_name = dept or "Không xác định"
                    stats_text += f"<tr><td>{dept_name}:</td><td>{count}</td></tr>"
            else:
                stats_text += "<tr><td colspan='2'>Chưa có dữ liệu</td></tr>"
            
            stats_text += f"""
</table>

<h3>Thông tin hệ thống:</h3>
<table>
<tr><td><b>Database:</b></td><td>{stats.get('database_file', 'N/A')}</td></tr>
<tr><td><b>Data root:</b></td><td>{stats.get('data_root', 'N/A')}</td></tr>
</table>

<p><i>Cập nhật lần cuối: {QTimer().singleShot.__self__.__class__.__name__}</i></p>
"""
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            logger.error(f"Lỗi update statistics: {e}")
            self.stats_label.setText(f"Lỗi tải thống kê: {e}")
    
    def on_patient_selected(self, patient):
        """Xử lý khi chọn bệnh nhân"""
        self.status_label.setText(f"Đã chọn: {patient.patient_name} ({patient.patient_id})")
        self.update_patient_count()
    
    def on_patient_double_clicked(self, patient):
        """Xử lý double click bệnh nhân"""
        # TODO: Mở patient workspace/viewer
        QMessageBox.information(
            self,
            "Patient Selected",
            f"Opening workspace for:\n{patient.patient_name} ({patient.patient_id})\n\nTính năng đang phát triển..."
        )
    
    def show_settings(self):
        """Hiển thị dialog settings"""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog đang phát triển...")
    
    def show_about(self):
        """Hiển thị dialog About"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def save_settings(self):
        """Lưu settings"""
        try:
            # Window geometry
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            
            # Current tab
            self.settings.setValue("currentTab", self.right_tabs.currentIndex())
            
        except Exception as e:
            logger.warning(f"Không thể lưu settings: {e}")
    
    def restore_settings(self):
        """Khôi phục settings"""
        try:
            # Window geometry
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            window_state = self.settings.value("windowState")
            if window_state:
                self.restoreState(window_state)
            
            # Current tab
            tab_index = self.settings.value("currentTab", 0, int)
            if 0 <= tab_index < self.right_tabs.count():
                self.right_tabs.setCurrentIndex(tab_index)
                
        except Exception as e:
            logger.warning(f"Không thể khôi phục settings: {e}")
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Save settings
            self.save_settings()
            
            # Confirm exit
            reply = QMessageBox.question(
                self,
                "Thoát ứng dụng",
                "Bạn có chắc chắn muốn thoát TPS?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                logger.info("Ứng dụng đang thoát...")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            logger.error(f"Lỗi khi thoát ứng dụng: {e}")
            event.accept()  # Force close nếu có lỗi
