"""
Module Image Workspace - Workspace chính cho Image Viewing và Visualization

Chức năng:
- Tích hợp tất cả image viewers và controls
- Layout responsive và customizable
- Save/restore workspace configurations
- Multi-monitor support
- Professional medical imaging interface như Eclipse TPS
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QDockWidget, QMainWindow, QFrame,
    QGroupBox, QLabel, QPushButton, QCheckBox,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
    QMessageBox, QProgressBar, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont, QKeySequence, QIcon

from .image_viewer_widget import ImageViewerWidget
from .mpr_viewer_widget import MPRViewerWidget
from .advanced_controls_widget import AdvancedControlsWidget
from .series_navigator_widget import SeriesNavigatorWidget
from ..core.patient_manager import PatientManager, Patient
from ..core.dicom_handler import DICOMSeries
from ..core.image_processor import WindowLevel

# Cấu hình logging
logger = logging.getLogger(__name__)


class ViewerMode:
    """Các chế độ viewer"""
    SINGLE = "single"
    DUAL = "dual" 
    QUAD = "quad"
    MPR = "mpr"
    CUSTOM = "custom"


class ImageWorkspace(QMainWindow):
    """
    Main workspace cho Image Viewing và Visualization
    Tương đương với imaging workspace trong Eclipse TPS
    """
    
    # Signals
    patient_loaded = pyqtSignal(object)  # Patient object
    series_loaded = pyqtSignal(object)   # DICOMSeries object
    viewer_mode_changed = pyqtSignal(str)  # mode name
    workspace_closed = pyqtSignal()
    
    def __init__(self, patient_manager: PatientManager = None, parent=None):
        super().__init__(parent)
        
        self.patient_manager = patient_manager or PatientManager()
        
        # Current data
        self.current_patient: Optional[Patient] = None
        self.current_series: Optional[DICOMSeries] = None
        self.current_image_data = None
        self.current_spacing = None
        self.current_origin = None
        
        # Viewers
        self.mpr_viewer: Optional[MPRViewerWidget] = None
        self.single_viewer: Optional[ImageViewerWidget] = None
        self.viewers: Dict[str, ImageViewerWidget] = {}
        
        # Controls
        self.advanced_controls: Optional[AdvancedControlsWidget] = None
        self.series_navigator: Optional[SeriesNavigatorWidget] = None
        
        # Current mode
        self.current_mode = ViewerMode.MPR
        
        # Dock widgets
        self.dock_widgets: Dict[str, QDockWidget] = {}
        
        # Settings
        self.settings = QSettings("TPS", "ImageWorkspace")
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_dock_widgets()
        self.setup_connections()
        self.restore_workspace()
        
        logger.info("ImageWorkspace initialized")
    
    def setup_ui(self):
        """Thiết lập giao diện chính"""
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Viewer container
        self.viewer_container = QFrame()
        self.viewer_container.setFrameStyle(QFrame.StyledPanel)
        
        # Viewer layout sẽ được setup trong switch_viewer_mode
        self.viewer_layout = QVBoxLayout()
        self.viewer_container.setLayout(self.viewer_layout)
        
        main_layout.addWidget(self.viewer_container, 1)  # Main area
        
        # Setup initial viewer mode
        self.switch_viewer_mode(ViewerMode.MPR)
        
        # Window properties
        self.setWindowTitle("TPS - Image Workspace")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Set window icon
        if Path("resources/icons/imaging.ico").exists():
            self.setWindowIcon(QIcon("resources/icons/imaging.ico"))
    
    def setup_menu_bar(self):
        """Thiết lập menu bar"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # Load Patient
        load_patient_action = QAction("Load &Patient", self)
        load_patient_action.setShortcut("Ctrl+P")
        load_patient_action.triggered.connect(self.show_patient_selector)
        file_menu.addAction(load_patient_action)
        
        # Load DICOM
        load_dicom_action = QAction("Load &DICOM", self)
        load_dicom_action.setShortcut("Ctrl+D")
        load_dicom_action.triggered.connect(self.load_dicom_folder)
        file_menu.addAction(load_dicom_action)
        
        file_menu.addSeparator()
        
        # Export Screenshots
        export_action = QAction("&Export Screenshots", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_screenshots)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Close Workspace
        close_action = QAction("&Close Workspace", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close_workspace)
        file_menu.addAction(close_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Viewer Modes
        mode_menu = view_menu.addMenu("Viewer &Mode")
        
        modes = [
            (ViewerMode.SINGLE, "Single View", "F1"),
            (ViewerMode.DUAL, "Dual View", "F2"), 
            (ViewerMode.QUAD, "Quad View", "F3"),
            (ViewerMode.MPR, "MPR View", "F4")
        ]
        
        for mode, name, shortcut in modes:
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, m=mode: self.switch_viewer_mode(m))
            mode_menu.addAction(action)
        
        view_menu.addSeparator()
        
        # Show/Hide Panels
        panels_menu = view_menu.addMenu("&Panels")
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Window/Level Presets
        wl_menu = tools_menu.addMenu("&Window/Level")
        
        presets = [
            ("Bone", WindowLevel(400, 1500, "Bone")),
            ("Soft Tissue", WindowLevel(50, 350, "Soft Tissue")),
            ("Lung", WindowLevel(-600, 1600, "Lung")),
            ("Brain", WindowLevel(40, 80, "Brain"))
        ]
        
        for name, wl in presets:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, w=wl: self.apply_window_level_preset(w))
            wl_menu.addAction(action)
        
        # Measurements
        measurements_action = QAction("&Measurements", self)
        measurements_action.setShortcut("Ctrl+M")
        measurements_action.triggered.connect(self.toggle_measurements)
        tools_menu.addAction(measurements_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # Shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
    
    def setup_toolbar(self):
        """Thiết lập toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Patient/Series info
        self.patient_info_label = QLabel("No patient loaded")
        toolbar.addWidget(self.patient_info_label)
        
        toolbar.addSeparator()
        
        # Viewer mode buttons
        single_action = QAction("Single", self)
        single_action.triggered.connect(lambda: self.switch_viewer_mode(ViewerMode.SINGLE))
        toolbar.addAction(single_action)
        
        dual_action = QAction("Dual", self)
        dual_action.triggered.connect(lambda: self.switch_viewer_mode(ViewerMode.DUAL))
        toolbar.addAction(dual_action)
        
        quad_action = QAction("Quad", self)
        quad_action.triggered.connect(lambda: self.switch_viewer_mode(ViewerMode.QUAD))
        toolbar.addAction(quad_action)
        
        mpr_action = QAction("MPR", self)
        mpr_action.triggered.connect(lambda: self.switch_viewer_mode(ViewerMode.MPR))
        toolbar.addAction(mpr_action)
        
        toolbar.addSeparator()
        
        # Quick tools
        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self.reset_all_views)
        toolbar.addAction(reset_action)
        
        fit_action = QAction("Fit", self)
        fit_action.triggered.connect(self.fit_to_window)
        toolbar.addAction(fit_action)
    
    def setup_status_bar(self):
        """Thiết lập status bar"""
        self.status_bar = self.statusBar()
        
        # Main status
        self.main_status_label = QLabel("Ready")
        self.status_bar.addWidget(self.main_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Mouse position
        self.position_label = QLabel("Position: (0, 0, 0)")
        self.status_bar.addPermanentWidget(self.position_label)
        
        # Pixel value
        self.pixel_value_label = QLabel("Value: --")
        self.status_bar.addPermanentWidget(self.pixel_value_label)
        
        # Zoom level
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
    
    def setup_dock_widgets(self):
        """Thiết lập dock widgets"""
        # Series Navigator Dock
        self.series_navigator = SeriesNavigatorWidget(self.patient_manager)
        nav_dock = QDockWidget("Series Navigator", self)
        nav_dock.setWidget(self.series_navigator)
        nav_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, nav_dock)
        self.dock_widgets["navigator"] = nav_dock
        
        # Advanced Controls Dock
        self.advanced_controls = AdvancedControlsWidget()
        controls_dock = QDockWidget("Advanced Controls", self)
        controls_dock.setWidget(self.advanced_controls)
        controls_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, controls_dock)
        self.dock_widgets["controls"] = controls_dock
        
        # Information Panel Dock
        info_widget = self.create_info_panel()
        info_dock = QDockWidget("Information", self)
        info_dock.setWidget(info_widget)
        info_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, info_dock)
        self.dock_widgets["info"] = info_dock
    
    def create_info_panel(self) -> QWidget:
        """Tạo information panel"""
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Patient Info
        patient_group = QGroupBox("Patient Information")
        patient_layout = QVBoxLayout()
        
        self.patient_details_label = QLabel("No patient loaded")
        self.patient_details_label.setWordWrap(True)
        patient_layout.addWidget(self.patient_details_label)
        
        patient_group.setLayout(patient_layout)
        layout.addWidget(patient_group)
        
        # Series Info
        series_group = QGroupBox("Series Information")
        series_layout = QVBoxLayout()
        
        self.series_details_label = QLabel("No series loaded")
        self.series_details_label.setWordWrap(True)
        series_layout.addWidget(self.series_details_label)
        
        series_group.setLayout(series_layout)
        layout.addWidget(series_group)
        
        # Image Info
        image_group = QGroupBox("Image Information")
        image_layout = QVBoxLayout()
        
        self.image_details_label = QLabel("No image loaded")
        self.image_details_label.setWordWrap(True)
        image_layout.addWidget(self.image_details_label)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Thiết lập kết nối signals"""
        if self.series_navigator:
            self.series_navigator.patient_changed.connect(self.on_patient_changed)
            self.series_navigator.series_selected.connect(self.on_series_selected)
            self.series_navigator.series_loaded.connect(self.on_series_loaded)
        
        if self.advanced_controls:
            self.advanced_controls.window_level_preset_changed.connect(self.on_window_level_changed)
            self.advanced_controls.zoom_changed.connect(self.on_zoom_changed)
            self.advanced_controls.rotation_changed.connect(self.on_rotation_changed)
    
    def switch_viewer_mode(self, mode: str):
        """Chuyển đổi chế độ viewer"""
        try:
            # Clear current viewers
            self.clear_viewer_container()
            
            # Create new viewers theo mode
            if mode == ViewerMode.SINGLE:
                self.setup_single_viewer()
            elif mode == ViewerMode.DUAL:
                self.setup_dual_viewer()
            elif mode == ViewerMode.QUAD:
                self.setup_quad_viewer()
            elif mode == ViewerMode.MPR:
                self.setup_mpr_viewer()
            else:
                logger.warning(f"Unknown viewer mode: {mode}")
                return
            
            self.current_mode = mode
            
            # Reload current data nếu có
            if self.current_image_data is not None:
                self.load_image_to_viewers()
            
            # Update UI
            if hasattr(self, 'main_status_label'):
                self.main_status_label.setText(f"Viewer mode: {mode}")
            
            # Emit signal
            self.viewer_mode_changed.emit(mode)
            
            logger.info(f"Switched to viewer mode: {mode}")
            
        except Exception as e:
            logger.error(f"Error switching viewer mode: {e}")
            QMessageBox.critical(self, "Error", f"Failed to switch viewer mode:\n{e}")
    
    def clear_viewer_container(self):
        """Clear viewer container"""
        # Remove all widgets từ layout
        while self.viewer_layout.count():
            child = self.viewer_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear viewer references
        self.mpr_viewer = None
        self.single_viewer = None
        self.viewers.clear()
    
    def setup_single_viewer(self):
        """Setup single viewer mode"""
        self.single_viewer = ImageViewerWidget("axial")
        self.viewers["main"] = self.single_viewer
        self.viewer_layout.addWidget(self.single_viewer)
    
    def setup_dual_viewer(self):
        """Setup dual viewer mode"""
        splitter = QSplitter(Qt.Horizontal)
        
        axial_viewer = ImageViewerWidget("axial")
        coronal_viewer = ImageViewerWidget("coronal")
        
        self.viewers["axial"] = axial_viewer
        self.viewers["coronal"] = coronal_viewer
        
        splitter.addWidget(axial_viewer)
        splitter.addWidget(coronal_viewer)
        splitter.setSizes([500, 500])
        
        self.viewer_layout.addWidget(splitter)
    
    def setup_quad_viewer(self):
        """Setup quad viewer mode"""
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top row
        top_splitter = QSplitter(Qt.Horizontal)
        axial_viewer = ImageViewerWidget("axial")
        coronal_viewer = ImageViewerWidget("coronal")
        top_splitter.addWidget(axial_viewer)
        top_splitter.addWidget(coronal_viewer)
        
        # Bottom row
        bottom_splitter = QSplitter(Qt.Horizontal)
        sagittal_viewer = ImageViewerWidget("sagittal")
        
        # 4th panel - info hoặc 3D
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        info_label = QLabel("Additional Information\nor 3D Rendering")
        info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_label)
        info_widget.setLayout(info_layout)
        
        bottom_splitter.addWidget(sagittal_viewer)
        bottom_splitter.addWidget(info_widget)
        
        # Add to main splitter
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(bottom_splitter)
        main_splitter.setSizes([400, 400])
        
        self.viewers["axial"] = axial_viewer
        self.viewers["coronal"] = coronal_viewer
        self.viewers["sagittal"] = sagittal_viewer
        
        self.viewer_layout.addWidget(main_splitter)
    
    def setup_mpr_viewer(self):
        """Setup MPR viewer mode"""
        self.mpr_viewer = MPRViewerWidget()
        self.viewer_layout.addWidget(self.mpr_viewer)
    
    def load_image_to_viewers(self):
        """Load current image data vào tất cả viewers"""
        if self.current_image_data is None:
            return
        
        try:
            if self.current_mode == ViewerMode.MPR and self.mpr_viewer:
                self.mpr_viewer.load_image_data(
                    self.current_image_data,
                    self.current_spacing,
                    self.current_origin
                )
            else:
                # Load vào individual viewers
                for viewer in self.viewers.values():
                    if isinstance(viewer, ImageViewerWidget):
                        viewer.load_image_data(
                            self.current_image_data,
                            self.current_spacing,
                            self.current_origin
                        )
            
            logger.info("Image data loaded to all viewers")
            
        except Exception as e:
            logger.error(f"Error loading image to viewers: {e}")
    
    def on_patient_changed(self, patient: Patient):
        """Handle patient change"""
        self.current_patient = patient
        
        # Update patient info display
        if patient:
            info_text = f"""
            <b>{patient.patient_name}</b> ({patient.patient_id})<br>
            Born: {patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else 'Unknown'}<br>
            Sex: {patient.sex or 'Unknown'}<br>
            Diagnosis: {patient.diagnosis or 'Not specified'}
            """
            self.patient_details_label.setText(info_text)
            self.patient_info_label.setText(f"{patient.patient_name} ({patient.patient_id})")
        else:
            self.patient_details_label.setText("No patient loaded")
            self.patient_info_label.setText("No patient loaded")
        
        # Clear series info
        self.series_details_label.setText("No series loaded")
        self.image_details_label.setText("No image loaded")
        
        # Emit signal
        self.patient_loaded.emit(patient)
        
        logger.info(f"Patient changed: {patient.patient_name if patient else 'None'}")
    
    def on_series_selected(self, series: DICOMSeries):
        """Handle series selection"""
        self.current_series = series
        
        if series:
            info_text = f"""
            <b>{series.series_description}</b><br>
            Modality: {series.modality}<br>
            Series: {series.series_number}<br>
            Slices: {series.slice_count}<br>
            Date: {series.series_date.strftime('%Y-%m-%d') if series.series_date else 'Unknown'}
            """
            self.series_details_label.setText(info_text)
        else:
            self.series_details_label.setText("No series selected")
    
    def on_series_loaded(self, image_array, spacing, origin):
        """Handle series loaded"""
        try:
            # Store image data
            self.current_image_data = image_array
            self.current_spacing = spacing
            self.current_origin = origin
            
            # Update image info
            if image_array is not None:
                info_text = f"""
                <b>Image Dimensions:</b> {image_array.shape}<br>
                <b>Data Type:</b> {image_array.dtype}<br>
                <b>Spacing:</b> {spacing}<br>
                <b>Origin:</b> {origin}<br>
                <b>Min/Max:</b> {image_array.min():.1f} / {image_array.max():.1f}
                """
                self.image_details_label.setText(info_text)
            
            # Load to viewers
            self.load_image_to_viewers()
            
            # Emit signal
            if self.current_series:
                self.series_loaded.emit(self.current_series)
            
            self.main_status_label.setText("Series loaded successfully")
            logger.info(f"Series loaded: shape={image_array.shape}")
            
        except Exception as e:
            logger.error(f"Error handling series loaded: {e}")
            self.main_status_label.setText(f"Error loading series: {e}")
    
    def on_window_level_changed(self, window_level: WindowLevel):
        """Handle window/level change từ advanced controls"""
        try:
            if self.current_mode == ViewerMode.MPR and self.mpr_viewer:
                # Apply to MPR viewer
                self.mpr_viewer.axial_viewer.set_window_level(window_level)
                self.mpr_viewer.coronal_viewer.set_window_level(window_level)
                self.mpr_viewer.sagittal_viewer.set_window_level(window_level)
            else:
                # Apply to individual viewers
                for viewer in self.viewers.values():
                    if isinstance(viewer, ImageViewerWidget):
                        viewer.set_window_level(window_level)
            
            logger.info(f"Window/Level applied: {window_level.name}")
            
        except Exception as e:
            logger.error(f"Error applying window/level: {e}")
    
    def on_zoom_changed(self, zoom_factor: float):
        """Handle zoom change"""
        self.zoom_label.setText(f"Zoom: {int(zoom_factor * 100)}%")
        # TODO: Apply zoom to viewers
    
    def on_rotation_changed(self, angle: float):
        """Handle rotation change"""
        # TODO: Apply rotation to viewers
        pass
    
    def show_patient_selector(self):
        """Show patient selector dialog"""
        # TODO: Implement patient selector dialog
        QMessageBox.information(self, "Patient Selector", "Patient selector dialog đang phát triển...")
    
    def load_dicom_folder(self):
        """Load DICOM từ folder"""
        if self.series_navigator:
            self.series_navigator.import_dicom_data()
    
    def export_screenshots(self):
        """Export screenshots của tất cả viewers"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import datetime
            
            # Get save location
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"TPS_Screenshots_{timestamp}"
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Screenshots",
                base_name,
                "PNG files (*.png)"
            )
            
            if not filename:
                return
            
            # Remove extension từ base name
            base_path = str(Path(filename).with_suffix(''))
            
            # Export theo mode
            if self.current_mode == ViewerMode.MPR and self.mpr_viewer:
                self.mpr_viewer.export_all_screenshots(base_path)
            else:
                for name, viewer in self.viewers.items():
                    if isinstance(viewer, ImageViewerWidget):
                        viewer.export_screenshot(f"{base_path}_{name}.png")
            
            QMessageBox.information(self, "Export Complete", f"Screenshots exported to:\n{base_path}_*.png")
            
        except Exception as e:
            logger.error(f"Error exporting screenshots: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export screenshots:\n{e}")
    
    def reset_all_views(self):
        """Reset tất cả views"""
        if self.current_mode == ViewerMode.MPR and self.mpr_viewer:
            self.mpr_viewer.reset_all_views()
        else:
            for viewer in self.viewers.values():
                if isinstance(viewer, ImageViewerWidget):
                    viewer.reset_view()
    
    def fit_to_window(self):
        """Fit tất cả images to window"""
        if self.current_mode == ViewerMode.MPR and self.mpr_viewer:
            self.mpr_viewer.reset_all_views()  # MPR reset includes fit
        else:
            for viewer in self.viewers.values():
                if isinstance(viewer, ImageViewerWidget):
                    viewer.fit_to_window()
    
    def apply_window_level_preset(self, window_level: WindowLevel):
        """Apply window/level preset to all viewers"""
        self.on_window_level_changed(window_level)
        
        # Also update advanced controls
        if self.advanced_controls:
            self.advanced_controls.set_window_level_preset(window_level)
    
    def toggle_measurements(self):
        """Toggle measurement tools"""
        if self.advanced_controls:
            # Switch to measurements tab
            # TODO: Implement tab switching in advanced controls
            pass
    
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>F1-F4:</b></td><td>Switch viewer modes</td></tr>
<tr><td><b>Ctrl+P:</b></td><td>Load patient</td></tr>
<tr><td><b>Ctrl+D:</b></td><td>Load DICOM</td></tr>
<tr><td><b>Ctrl+E:</b></td><td>Export screenshots</td></tr>
<tr><td><b>Ctrl+M:</b></td><td>Toggle measurements</td></tr>
<tr><td><b>Ctrl+W:</b></td><td>Close workspace</td></tr>
</table>

<h4>Mouse Controls:</h4>
<table>
<tr><td><b>Mouse Wheel:</b></td><td>Scroll through slices</td></tr>
<tr><td><b>Shift + Mouse:</b></td><td>Adjust Window/Level</td></tr>
<tr><td><b>Ctrl + Mouse:</b></td><td>Zoom</td></tr>
<tr><td><b>Alt + Mouse:</b></td><td>Pan</td></tr>
</table>
        """
        
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def save_workspace(self):
        """Save workspace configuration"""
        try:
            # Save dock widget states
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("windowState", self.saveState())
            
            # Save current mode
            self.settings.setValue("viewerMode", self.current_mode)
            
            # Save current patient/series (by ID)
            if self.current_patient:
                self.settings.setValue("currentPatient", self.current_patient.patient_id)
            
            logger.info("Workspace configuration saved")
            
        except Exception as e:
            logger.error(f"Error saving workspace: {e}")
    
    def restore_workspace(self):
        """Restore workspace configuration"""
        try:
            # Restore dock widget states
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            
            window_state = self.settings.value("windowState")
            if window_state:
                self.restoreState(window_state)
            
            # Restore viewer mode
            saved_mode = self.settings.value("viewerMode", ViewerMode.MPR)
            if saved_mode != self.current_mode:
                self.switch_viewer_mode(saved_mode)
            
            logger.info("Workspace configuration restored")
            
        except Exception as e:
            logger.error(f"Error restoring workspace: {e}")
    
    def close_workspace(self):
        """Close workspace"""
        reply = QMessageBox.question(
            self,
            "Close Workspace",
            "Are you sure you want to close the Image Workspace?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_workspace()
            self.workspace_closed.emit()
            self.close()
    
    def closeEvent(self, event):
        """Handle close event"""
        self.save_workspace()
        self.workspace_closed.emit()
        event.accept()
        logger.info("Image Workspace closed")
