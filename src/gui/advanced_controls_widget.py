"""
Module Advanced Controls Widget - Điều khiển nâng cao cho Image Viewer

Chức năng:
- Window/Level presets và custom controls
- Zoom, Pan, Rotate tools
- Measurement tools (distance, angle, area)
- Annotations và markers
- Image filters và enhancements
- Cine mode cho time series
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
import math

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QSlider, QSpinBox,
    QComboBox, QCheckBox, QLineEdit, QTextEdit,
    QTabWidget, QButtonGroup, QRadioButton, QFrame,
    QColorDialog, QFontDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap

from ..core.image_processor import ImageProcessor, WindowLevel

# Cấu hình logging
logger = logging.getLogger(__name__)


class MeasurementTool(Enum):
    """Các công cụ đo lường"""
    NONE = "none"
    DISTANCE = "distance"
    ANGLE = "angle"
    AREA = "area"
    VOLUME = "volume"
    PROFILE = "profile"


class AnnotationTool(Enum):
    """Các công cụ chú thích"""
    NONE = "none"
    TEXT = "text"
    ARROW = "arrow"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    FREEHAND = "freehand"


class ImageFilter(Enum):
    """Các bộ lọc ảnh"""
    NONE = "none"
    GAUSSIAN_BLUR = "gaussian_blur"
    SHARPEN = "sharpen"
    EDGE_ENHANCE = "edge_enhance"
    MEDIAN = "median"
    BILATERAL = "bilateral"


class AdvancedControlsWidget(QWidget):
    """
    Widget điều khiển nâng cao cho image viewer
    Tương đương với advanced controls trong Eclipse TPS
    """
    
    # Signals
    window_level_preset_changed = pyqtSignal(object)  # WindowLevel object
    measurement_tool_changed = pyqtSignal(str)  # tool name
    annotation_tool_changed = pyqtSignal(str)  # tool name
    image_filter_changed = pyqtSignal(str, dict)  # filter name, parameters
    zoom_changed = pyqtSignal(float)  # zoom factor
    rotation_changed = pyqtSignal(float)  # rotation angle
    cine_mode_changed = pyqtSignal(bool, int)  # enabled, speed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current states
        self.current_measurement_tool = MeasurementTool.NONE
        self.current_annotation_tool = AnnotationTool.NONE
        self.current_filter = ImageFilter.NONE
        self.current_zoom = 1.0
        self.current_rotation = 0.0
        
        # Cine mode
        self.cine_enabled = False
        self.cine_speed = 10  # frames per second
        self.cine_timer = QTimer()
        self.cine_timer.timeout.connect(self.on_cine_frame)
        
        # Image processor
        self.image_processor = ImageProcessor()
        
        self.setup_ui()
        self.setup_connections()
        
        logger.info("AdvancedControlsWidget initialized")
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Advanced Controls")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Tab widget cho các nhóm controls
        tab_widget = QTabWidget()
        
        # Tab 1: Window/Level & Display
        display_tab = self.create_display_tab()
        tab_widget.addTab(display_tab, "Display")
        
        # Tab 2: Measurements
        measurement_tab = self.create_measurement_tab()
        tab_widget.addTab(measurement_tab, "Measurements")
        
        # Tab 3: Annotations
        annotation_tab = self.create_annotation_tab()
        tab_widget.addTab(annotation_tab, "Annotations")
        
        # Tab 4: Filters & Enhancement
        filter_tab = self.create_filter_tab()
        tab_widget.addTab(filter_tab, "Filters")
        
        # Tab 5: Navigation & Cine
        navigation_tab = self.create_navigation_tab()
        tab_widget.addTab(navigation_tab, "Navigation")
        
        layout.addWidget(tab_widget)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setMaximumWidth(350)  # Limit width to keep compact
    
    def create_display_tab(self) -> QWidget:
        """Tạo tab Display controls"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Window/Level Presets
        wl_group = QGroupBox("Window/Level Presets")
        wl_layout = QGridLayout()
        
        # CT Presets
        ct_presets = [
            ("Bone", WindowLevel(400, 1500, "Bone")),
            ("Soft Tissue", WindowLevel(50, 350, "Soft Tissue")),
            ("Lung", WindowLevel(-600, 1600, "Lung")),
            ("Brain", WindowLevel(40, 80, "Brain")),
            ("Abdomen", WindowLevel(60, 400, "Abdomen")),
            ("Mediastinum", WindowLevel(50, 350, "Mediastinum"))
        ]
        
        row = 0
        for i, (name, wl) in enumerate(ct_presets):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, w=wl: self.set_window_level_preset(w))
            wl_layout.addWidget(btn, row, i % 3)
            if (i + 1) % 3 == 0:
                row += 1
        
        # MRI Presets
        wl_layout.addWidget(QLabel("MRI:"), row + 1, 0)
        mri_presets = [
            ("T1", WindowLevel(500, 1000, "T1")),
            ("T2", WindowLevel(1000, 2000, "T2")),
            ("FLAIR", WindowLevel(800, 1600, "FLAIR"))
        ]
        
        for i, (name, wl) in enumerate(mri_presets):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, w=wl: self.set_window_level_preset(w))
            wl_layout.addWidget(btn, row + 2, i)
        
        wl_group.setLayout(wl_layout)
        layout.addWidget(wl_group)
        
        # Custom Window/Level
        custom_wl_group = QGroupBox("Custom Window/Level")
        custom_layout = QGridLayout()
        
        # Window
        custom_layout.addWidget(QLabel("Window:"), 0, 0)
        self.custom_window_spinbox = QSpinBox()
        self.custom_window_spinbox.setRange(1, 4000)
        self.custom_window_spinbox.setValue(255)
        custom_layout.addWidget(self.custom_window_spinbox, 0, 1)
        
        # Level
        custom_layout.addWidget(QLabel("Level:"), 1, 0)
        self.custom_level_spinbox = QSpinBox()
        self.custom_level_spinbox.setRange(-1000, 3000)
        self.custom_level_spinbox.setValue(127)
        custom_layout.addWidget(self.custom_level_spinbox, 1, 1)
        
        # Apply button
        apply_custom_btn = QPushButton("Apply")
        apply_custom_btn.clicked.connect(self.apply_custom_window_level)
        custom_layout.addWidget(apply_custom_btn, 2, 0, 1, 2)
        
        custom_wl_group.setLayout(custom_layout)
        layout.addWidget(custom_wl_group)
        
        # Zoom & Rotation
        transform_group = QGroupBox("Zoom & Rotation")
        transform_layout = QGridLayout()
        
        # Zoom
        transform_layout.addWidget(QLabel("Zoom:"), 0, 0)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 10% to 500%
        self.zoom_slider.setValue(100)  # 100%
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        transform_layout.addWidget(self.zoom_slider, 0, 1)
        
        self.zoom_label = QLabel("100%")
        transform_layout.addWidget(self.zoom_label, 0, 2)
        
        # Rotation
        transform_layout.addWidget(QLabel("Rotation:"), 1, 0)
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        transform_layout.addWidget(self.rotation_slider, 1, 1)
        
        self.rotation_label = QLabel("0°")
        transform_layout.addWidget(self.rotation_label, 1, 2)
        
        # Reset buttons
        reset_layout = QHBoxLayout()
        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        reset_layout.addWidget(reset_zoom_btn)
        
        reset_rotation_btn = QPushButton("Reset Rotation")
        reset_rotation_btn.clicked.connect(self.reset_rotation)
        reset_layout.addWidget(reset_rotation_btn)
        
        transform_layout.addLayout(reset_layout, 2, 0, 1, 3)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_measurement_tab(self) -> QWidget:
        """Tạo tab Measurement tools"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tool Selection
        tool_group = QGroupBox("Measurement Tools")
        tool_layout = QVBoxLayout()
        
        self.measurement_tool_group = QButtonGroup()
        
        tools = [
            (MeasurementTool.NONE, "None", "No measurement"),
            (MeasurementTool.DISTANCE, "Distance", "Measure distance between two points"),
            (MeasurementTool.ANGLE, "Angle", "Measure angle between three points"),
            (MeasurementTool.AREA, "Area", "Measure area of region"),
            (MeasurementTool.VOLUME, "Volume", "Measure volume (3D)"),
            (MeasurementTool.PROFILE, "Profile", "Intensity profile along line")
        ]
        
        for tool, name, tooltip in tools:
            radio = QRadioButton(name)
            radio.setToolTip(tooltip)
            radio.clicked.connect(lambda checked, t=tool: self.set_measurement_tool(t))
            self.measurement_tool_group.addButton(radio)
            tool_layout.addWidget(radio)
        
        # Set default
        self.measurement_tool_group.buttons()[0].setChecked(True)
        
        tool_group.setLayout(tool_layout)
        layout.addWidget(tool_group)
        
        # Measurement Results
        results_group = QGroupBox("Measurement Results")
        results_layout = QVBoxLayout()
        
        self.measurement_results = QTextEdit()
        self.measurement_results.setMaximumHeight(150)
        self.measurement_results.setReadOnly(True)
        results_layout.addWidget(self.measurement_results)
        
        # Clear measurements button
        clear_btn = QPushButton("Clear All Measurements")
        clear_btn.clicked.connect(self.clear_measurements)
        results_layout.addWidget(clear_btn)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Measurement Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout()
        
        # Units
        settings_layout.addWidget(QLabel("Units:"), 0, 0)
        self.units_combo = QComboBox()
        self.units_combo.addItems(["mm", "cm", "pixels"])
        settings_layout.addWidget(self.units_combo, 0, 1)
        
        # Precision
        settings_layout.addWidget(QLabel("Decimal Places:"), 1, 0)
        self.precision_spinbox = QSpinBox()
        self.precision_spinbox.setRange(0, 5)
        self.precision_spinbox.setValue(2)
        settings_layout.addWidget(self.precision_spinbox, 1, 1)
        
        # Show labels
        self.show_labels_check = QCheckBox("Show Labels")
        self.show_labels_check.setChecked(True)
        settings_layout.addWidget(self.show_labels_check, 2, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_annotation_tab(self) -> QWidget:
        """Tạo tab Annotation tools"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tool Selection
        tool_group = QGroupBox("Annotation Tools")
        tool_layout = QVBoxLayout()
        
        self.annotation_tool_group = QButtonGroup()
        
        tools = [
            (AnnotationTool.NONE, "None"),
            (AnnotationTool.TEXT, "Text"),
            (AnnotationTool.ARROW, "Arrow"),
            (AnnotationTool.CIRCLE, "Circle"),
            (AnnotationTool.RECTANGLE, "Rectangle"),
            (AnnotationTool.FREEHAND, "Freehand")
        ]
        
        for tool, name in tools:
            radio = QRadioButton(name)
            radio.clicked.connect(lambda checked, t=tool: self.set_annotation_tool(t))
            self.annotation_tool_group.addButton(radio)
            tool_layout.addWidget(radio)
        
        # Set default
        self.annotation_tool_group.buttons()[0].setChecked(True)
        
        tool_group.setLayout(tool_layout)
        layout.addWidget(tool_group)
        
        # Text Settings
        text_group = QGroupBox("Text Settings")
        text_layout = QGridLayout()
        
        # Font
        text_layout.addWidget(QLabel("Font:"), 0, 0)
        self.font_btn = QPushButton("Select Font")
        self.font_btn.clicked.connect(self.select_font)
        text_layout.addWidget(self.font_btn, 0, 1)
        
        # Color
        text_layout.addWidget(QLabel("Color:"), 1, 0)
        self.color_btn = QPushButton()
        self.color_btn.setStyleSheet("background-color: yellow;")
        self.color_btn.clicked.connect(self.select_color)
        text_layout.addWidget(self.color_btn, 1, 1)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # Annotation List
        list_group = QGroupBox("Annotations")
        list_layout = QVBoxLayout()
        
        self.annotation_list = QTextEdit()
        self.annotation_list.setMaximumHeight(100)
        self.annotation_list.setReadOnly(True)
        list_layout.addWidget(self.annotation_list)
        
        # Clear annotations button
        clear_ann_btn = QPushButton("Clear All Annotations")
        clear_ann_btn.clicked.connect(self.clear_annotations)
        list_layout.addWidget(clear_ann_btn)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_filter_tab(self) -> QWidget:
        """Tạo tab Image filters"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter Selection
        filter_group = QGroupBox("Image Filters")
        filter_layout = QVBoxLayout()
        
        self.filter_combo = QComboBox()
        filters = [
            (ImageFilter.NONE, "None"),
            (ImageFilter.GAUSSIAN_BLUR, "Gaussian Blur"),
            (ImageFilter.SHARPEN, "Sharpen"),
            (ImageFilter.EDGE_ENHANCE, "Edge Enhancement"),
            (ImageFilter.MEDIAN, "Median Filter"),
            (ImageFilter.BILATERAL, "Bilateral Filter")
        ]
        
        for filter_type, name in filters:
            self.filter_combo.addItem(name, filter_type)
        
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Filter Parameters
        params_group = QGroupBox("Filter Parameters")
        params_layout = QGridLayout()
        
        # Gaussian Blur - Sigma
        params_layout.addWidget(QLabel("Sigma:"), 0, 0)
        self.sigma_slider = QSlider(Qt.Horizontal)
        self.sigma_slider.setRange(1, 50)
        self.sigma_slider.setValue(10)
        params_layout.addWidget(self.sigma_slider, 0, 1)
        
        self.sigma_label = QLabel("1.0")
        params_layout.addWidget(self.sigma_label, 0, 2)
        
        # Sharpen - Amount
        params_layout.addWidget(QLabel("Amount:"), 1, 0)
        self.amount_slider = QSlider(Qt.Horizontal)
        self.amount_slider.setRange(1, 200)
        self.amount_slider.setValue(100)
        params_layout.addWidget(self.amount_slider, 1, 1)
        
        self.amount_label = QLabel("100%")
        params_layout.addWidget(self.amount_label, 1, 2)
        
        # Apply button
        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.clicked.connect(self.apply_filter)
        params_layout.addWidget(apply_filter_btn, 2, 0, 1, 3)
        
        # Reset button
        reset_filter_btn = QPushButton("Reset to Original")
        reset_filter_btn.clicked.connect(self.reset_filter)
        params_layout.addWidget(reset_filter_btn, 3, 0, 1, 3)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_navigation_tab(self) -> QWidget:
        """Tạo tab Navigation & Cine"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Cine Mode
        cine_group = QGroupBox("Cine Mode")
        cine_layout = QGridLayout()
        
        # Enable cine
        self.cine_check = QCheckBox("Enable Cine Mode")
        self.cine_check.toggled.connect(self.toggle_cine_mode)
        cine_layout.addWidget(self.cine_check, 0, 0, 1, 2)
        
        # Speed control
        cine_layout.addWidget(QLabel("Speed (FPS):"), 1, 0)
        self.cine_speed_slider = QSlider(Qt.Horizontal)
        self.cine_speed_slider.setRange(1, 30)
        self.cine_speed_slider.setValue(10)
        self.cine_speed_slider.valueChanged.connect(self.on_cine_speed_changed)
        cine_layout.addWidget(self.cine_speed_slider, 1, 1)
        
        self.cine_speed_label = QLabel("10 FPS")
        cine_layout.addWidget(self.cine_speed_label, 1, 2)
        
        # Direction
        cine_layout.addWidget(QLabel("Direction:"), 2, 0)
        self.cine_direction_combo = QComboBox()
        self.cine_direction_combo.addItems(["Forward", "Backward", "Bounce"])
        cine_layout.addWidget(self.cine_direction_combo, 2, 1)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_cine)
        control_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pause_cine)
        control_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self.stop_cine)
        control_layout.addWidget(self.stop_btn)
        
        cine_layout.addLayout(control_layout, 3, 0, 1, 3)
        
        cine_group.setLayout(cine_layout)
        layout.addWidget(cine_group)
        
        # Navigation shortcuts
        shortcuts_group = QGroupBox("Navigation Shortcuts")
        shortcuts_layout = QGridLayout()
        
        shortcuts_layout.addWidget(QLabel("Mouse Wheel:"), 0, 0)
        shortcuts_layout.addWidget(QLabel("Scroll through slices"), 0, 1)
        
        shortcuts_layout.addWidget(QLabel("Shift + Mouse:"), 1, 0)
        shortcuts_layout.addWidget(QLabel("Window/Level"), 1, 1)
        
        shortcuts_layout.addWidget(QLabel("Ctrl + Mouse:"), 2, 0)
        shortcuts_layout.addWidget(QLabel("Zoom"), 2, 1)
        
        shortcuts_layout.addWidget(QLabel("Alt + Mouse:"), 3, 0)
        shortcuts_layout.addWidget(QLabel("Pan"), 3, 1)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        widget.setLayout(layout)
        return widget
    
    def setup_connections(self):
        """Setup signal connections"""
        # Slider connections for real-time updates
        self.sigma_slider.valueChanged.connect(
            lambda v: self.sigma_label.setText(f"{v/10:.1f}")
        )
        self.amount_slider.valueChanged.connect(
            lambda v: self.amount_label.setText(f"{v}%")
        )
    
    def set_window_level_preset(self, window_level: WindowLevel):
        """Áp dụng window/level preset"""
        self.window_level_preset_changed.emit(window_level)
        logger.info(f"Applied W/L preset: {window_level.name}")
    
    def apply_custom_window_level(self):
        """Áp dụng custom window/level"""
        window = self.custom_window_spinbox.value()
        level = self.custom_level_spinbox.value()
        
        wl = WindowLevel(center=level, width=window, name="Custom")
        self.window_level_preset_changed.emit(wl)
        
        logger.info(f"Applied custom W/L: W={window}, L={level}")
    
    def on_zoom_changed(self, value: int):
        """Handle zoom slider change"""
        zoom_factor = value / 100.0
        self.current_zoom = zoom_factor
        self.zoom_label.setText(f"{value}%")
        self.zoom_changed.emit(zoom_factor)
    
    def on_rotation_changed(self, value: int):
        """Handle rotation slider change"""
        self.current_rotation = value
        self.rotation_label.setText(f"{value}°")
        self.rotation_changed.emit(float(value))
    
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_slider.setValue(100)
    
    def reset_rotation(self):
        """Reset rotation to 0°"""
        self.rotation_slider.setValue(0)
    
    def set_measurement_tool(self, tool: MeasurementTool):
        """Set active measurement tool"""
        self.current_measurement_tool = tool
        self.measurement_tool_changed.emit(tool.value)
        logger.info(f"Measurement tool changed: {tool.value}")
    
    def set_annotation_tool(self, tool: AnnotationTool):
        """Set active annotation tool"""
        self.current_annotation_tool = tool
        self.annotation_tool_changed.emit(tool.value)
        logger.info(f"Annotation tool changed: {tool.value}")
    
    def clear_measurements(self):
        """Clear all measurements"""
        self.measurement_results.clear()
        logger.info("All measurements cleared")
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.annotation_list.clear()
        logger.info("All annotations cleared")
    
    def select_font(self):
        """Open font selection dialog"""
        font, ok = QFontDialog.getFont(QFont("Arial", 12), self)
        if ok:
            self.font_btn.setText(f"{font.family()} {font.pointSize()}pt")
            logger.info(f"Font selected: {font.family()} {font.pointSize()}pt")
    
    def select_color(self):
        """Open color selection dialog"""
        color = QColorDialog.getColor(Qt.yellow, self)
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            logger.info(f"Color selected: {color.name()}")
    
    def on_filter_changed(self):
        """Handle filter selection change"""
        filter_data = self.filter_combo.currentData()
        if filter_data:
            self.current_filter = filter_data
            logger.info(f"Filter changed: {filter_data.value}")
    
    def apply_filter(self):
        """Apply selected filter với parameters"""
        if self.current_filter == ImageFilter.NONE:
            return
        
        # Get parameters
        params = {}
        
        if self.current_filter == ImageFilter.GAUSSIAN_BLUR:
            params['sigma'] = self.sigma_slider.value() / 10.0
        elif self.current_filter == ImageFilter.SHARPEN:
            params['amount'] = self.amount_slider.value() / 100.0
        
        self.image_filter_changed.emit(self.current_filter.value, params)
        logger.info(f"Applied filter: {self.current_filter.value} with params: {params}")
    
    def reset_filter(self):
        """Reset to original image (no filter)"""
        self.filter_combo.setCurrentIndex(0)  # None
        self.image_filter_changed.emit(ImageFilter.NONE.value, {})
        logger.info("Filter reset to original image")
    
    def toggle_cine_mode(self, enabled: bool):
        """Toggle cine mode on/off"""
        self.cine_enabled = enabled
        self.cine_mode_changed.emit(enabled, self.cine_speed)
        
        # Enable/disable controls
        self.cine_speed_slider.setEnabled(enabled)
        self.cine_direction_combo.setEnabled(enabled)
        self.play_btn.setEnabled(enabled)
        self.pause_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        
        logger.info(f"Cine mode: {'enabled' if enabled else 'disabled'}")
    
    def on_cine_speed_changed(self, value: int):
        """Handle cine speed change"""
        self.cine_speed = value
        self.cine_speed_label.setText(f"{value} FPS")
        
        # Update timer interval if running
        if self.cine_timer.isActive():
            self.cine_timer.setInterval(1000 // value)
        
        self.cine_mode_changed.emit(self.cine_enabled, value)
    
    def play_cine(self):
        """Start cine playback"""
        if self.cine_enabled:
            interval = 1000 // self.cine_speed  # Convert FPS to milliseconds
            self.cine_timer.start(interval)
            self.play_btn.setText("▶ Playing...")
            logger.info("Cine playback started")
    
    def pause_cine(self):
        """Pause cine playback"""
        self.cine_timer.stop()
        self.play_btn.setText("▶ Play")
        logger.info("Cine playback paused")
    
    def stop_cine(self):
        """Stop cine playback"""
        self.cine_timer.stop()
        self.play_btn.setText("▶ Play")
        # TODO: Reset to first slice
        logger.info("Cine playback stopped")
    
    def on_cine_frame(self):
        """Handle cine frame advance"""
        # TODO: Advance to next slice
        # This will be connected to the image viewer
        pass
    
    def add_measurement_result(self, measurement_type: str, value: str, unit: str = "mm"):
        """Thêm kết quả đo lường vào display"""
        precision = self.precision_spinbox.value()
        result_text = f"{measurement_type}: {value} {unit}\n"
        
        self.measurement_results.append(result_text)
        logger.info(f"Measurement added: {result_text.strip()}")
    
    def add_annotation(self, annotation_type: str, text: str = ""):
        """Thêm annotation vào display"""
        if text:
            result_text = f"{annotation_type}: {text}\n"
        else:
            result_text = f"{annotation_type} annotation added\n"
        
        self.annotation_list.append(result_text)
        logger.info(f"Annotation added: {result_text.strip()}")
    
    def get_measurement_settings(self) -> Dict[str, Any]:
        """Lấy current measurement settings"""
        return {
            'units': self.units_combo.currentText(),
            'precision': self.precision_spinbox.value(),
            'show_labels': self.show_labels_check.isChecked()
        }
    
    def get_current_tool_states(self) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại của tất cả tools"""
        return {
            'measurement_tool': self.current_measurement_tool.value,
            'annotation_tool': self.current_annotation_tool.value,
            'filter': self.current_filter.value,
            'zoom': self.current_zoom,
            'rotation': self.current_rotation,
            'cine_enabled': self.cine_enabled,
            'cine_speed': self.cine_speed
        }
