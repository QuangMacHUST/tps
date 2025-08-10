"""
Module MPR Viewer Widget - Multi-Planar Reconstruction Viewer

Chức năng:
- Hiển thị 3 views đồng thời: Axial, Coronal, Sagittal
- Synchronized navigation giữa các views
- 3D volume rendering
- Crosshair cursors
- Coordinated zoom và pan
"""

import logging
from typing import Optional, Tuple, List
import numpy as np

try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, QLabel, QFrame, QPushButton, QCheckBox,
    QSlider, QSpinBox, QGroupBox, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from .image_viewer_widget import ImageViewerWidget
from ..core.image_processor import ImageProcessor, WindowLevel

# Cấu hình logging
logger = logging.getLogger(__name__)


class VolumeRenderWidget(QWidget):
    """Widget cho 3D volume rendering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not VTK_AVAILABLE:
            self._setup_fallback_ui()
            return
        
        self.image_data = None
        self.volume_mapper = None
        self.volume_actor = None
        self.renderer = None
        self.render_window = None
        
        self.setup_ui()
        self.setup_vtk_3d()
    
    def _setup_fallback_ui(self):
        """Setup fallback UI khi VTK không available"""
        layout = QVBoxLayout()
        
        warning_label = QLabel("⚠️ 3D Volume Rendering\nVTK Library không khả dụng")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        self.setLayout(layout)
        return
    
    def setup_ui(self):
        """Thiết lập giao diện 3D"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("3D Volume Rendering")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 3D controls
        self.volume_rendering_check = QCheckBox("Volume Rendering")
        self.volume_rendering_check.setChecked(True)
        self.volume_rendering_check.toggled.connect(self.toggle_volume_rendering)
        header_layout.addWidget(self.volume_rendering_check)
        
        self.surface_rendering_check = QCheckBox("Surface Rendering")
        self.surface_rendering_check.toggled.connect(self.toggle_surface_rendering)
        header_layout.addWidget(self.surface_rendering_check)
        
        layout.addLayout(header_layout)
        
        # 3D VTK container
        self.vtk_3d_container = QFrame()
        self.vtk_3d_container.setFrameStyle(QFrame.StyledPanel)
        self.vtk_3d_container.setMinimumSize(400, 400)
        
        self.vtk_3d_layout = QVBoxLayout()
        self.vtk_3d_container.setLayout(self.vtk_3d_layout)
        
        layout.addWidget(self.vtk_3d_container, 1)
        
        # 3D Controls
        controls_group = QGroupBox("3D Controls")
        controls_layout = QGridLayout()
        
        # Opacity control
        controls_layout.addWidget(QLabel("Opacity:"), 0, 0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        controls_layout.addWidget(self.opacity_slider, 0, 1)
        
        # Threshold controls
        controls_layout.addWidget(QLabel("Threshold:"), 1, 0)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(4000)
        self.threshold_slider.setValue(100)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        controls_layout.addWidget(self.threshold_slider, 1, 1)
        
        # Reset view button
        reset_3d_btn = QPushButton("Reset 3D View")
        reset_3d_btn.clicked.connect(self.reset_3d_view)
        controls_layout.addWidget(reset_3d_btn, 2, 0, 1, 2)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        self.setLayout(layout)
    
    def setup_vtk_3d(self):
        """Setup VTK cho 3D rendering"""
        if not VTK_AVAILABLE:
            return
        
        try:
            from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
            
            # Create 3D VTK widget
            self.vtk_3d_widget = QVTKRenderWindowInteractor(self.vtk_3d_container)
            self.vtk_3d_layout.addWidget(self.vtk_3d_widget)
            
            # Setup 3D renderer
            self.renderer = vtk.vtkRenderer()
            self.renderer.SetBackground(0.1, 0.1, 0.2)  # Dark blue background
            
            self.render_window = self.vtk_3d_widget.GetRenderWindow()
            self.render_window.AddRenderer(self.renderer)
            
            # Setup interactor
            self.interactor = self.vtk_3d_widget.GetRenderWindow().GetInteractor()
            
            # Use trackball camera style for 3D
            style = vtk.vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(style)
            
            logger.info("3D VTK setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up 3D VTK: {e}")
    
    def load_volume_data(self, image_data):
        """Load volume data cho 3D rendering"""
        if not VTK_AVAILABLE or not image_data:
            return
        
        try:
            self.image_data = image_data
            
            # Create volume mapper
            self.volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
            self.volume_mapper.SetInputData(image_data)
            
            # Create volume properties
            volume_property = vtk.vtkVolumeProperty()
            volume_property.SetInterpolationTypeToLinear()
            
            # Create opacity transfer function
            opacity_tf = vtk.vtkPiecewiseFunction()
            opacity_tf.AddPoint(0, 0.0)
            opacity_tf.AddPoint(500, 0.15)
            opacity_tf.AddPoint(1000, 0.85)
            opacity_tf.AddPoint(1500, 0.95)
            
            # Create color transfer function
            color_tf = vtk.vtkColorTransferFunction()
            color_tf.AddRGBPoint(0, 0.0, 0.0, 0.0)
            color_tf.AddRGBPoint(500, 1.0, 0.5, 0.3)
            color_tf.AddRGBPoint(1000, 1.0, 1.0, 0.9)
            color_tf.AddRGBPoint(1500, 1.0, 1.0, 1.0)
            
            volume_property.SetScalarOpacity(opacity_tf)
            volume_property.SetColor(color_tf)
            
            # Create volume actor
            self.volume_actor = vtk.vtkVolume()
            self.volume_actor.SetMapper(self.volume_mapper)
            self.volume_actor.SetProperty(volume_property)
            
            # Add to renderer
            if self.renderer:
                self.renderer.RemoveAllViewProps()
                self.renderer.AddVolume(self.volume_actor)
                self.renderer.ResetCamera()
                
                if self.render_window:
                    self.render_window.Render()
            
            logger.info("3D volume data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading 3D volume data: {e}")
    
    def toggle_volume_rendering(self, enabled: bool):
        """Toggle volume rendering on/off"""
        if self.volume_actor and self.renderer:
            self.volume_actor.SetVisibility(enabled)
            if self.render_window:
                self.render_window.Render()
    
    def toggle_surface_rendering(self, enabled: bool):
        """Toggle surface rendering on/off"""
        # TODO: Implement surface rendering with marching cubes
        pass
    
    def on_opacity_changed(self, value: int):
        """Handle opacity slider change"""
        if self.volume_actor:
            opacity = value / 100.0
            self.volume_actor.GetProperty().SetScalarOpacity(0, opacity)
            if self.render_window:
                self.render_window.Render()
    
    def on_threshold_changed(self, value: int):
        """Handle threshold change"""
        # TODO: Implement threshold adjustment
        pass
    
    def reset_3d_view(self):
        """Reset 3D camera view"""
        if self.renderer:
            self.renderer.ResetCamera()
            if self.render_window:
                self.render_window.Render()


class MPRViewerWidget(QWidget):
    """
    Multi-Planar Reconstruction Viewer
    Tương đương với MPR viewer trong Eclipse TPS
    """
    
    # Signals
    crosshair_moved = pyqtSignal(float, float, float)  # x, y, z coordinates
    slice_changed_any = pyqtSignal(str, int)  # orientation, slice
    window_level_changed_any = pyqtSignal(float, float)  # center, width
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Image data
        self.image_data = None
        self.image_array = None
        self.spacing = None
        self.origin = None
        
        # Current crosshair position
        self.crosshair_position = [0, 0, 0]
        
        # Synchronized window/level
        self.sync_window_level = True
        
        # Individual viewers
        self.axial_viewer = None
        self.coronal_viewer = None
        self.sagittal_viewer = None
        self.volume_widget = None
        
        self.setup_ui()
        
        logger.info("MPRViewerWidget initialized")
    
    def setup_ui(self):
        """Thiết lập giao diện MPR"""
        layout = QVBoxLayout()
        
        # Header với controls
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Multi-Planar Reconstruction (MPR)")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Global controls
        self.sync_wl_check = QCheckBox("Sync W/L")
        self.sync_wl_check.setChecked(True)
        self.sync_wl_check.toggled.connect(self.toggle_sync_window_level)
        header_layout.addWidget(self.sync_wl_check)
        
        self.show_crosshair_check = QCheckBox("Show Crosshairs")
        self.show_crosshair_check.setChecked(True)
        header_layout.addWidget(self.show_crosshair_check)
        
        reset_all_btn = QPushButton("Reset All Views")
        reset_all_btn.clicked.connect(self.reset_all_views)
        header_layout.addWidget(reset_all_btn)
        
        layout.addLayout(header_layout)
        
        # Main splitter cho các views
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: 3 planar views trong grid
        left_widget = QWidget()
        left_layout = QGridLayout()
        
        # Create individual viewers
        self.axial_viewer = ImageViewerWidget("axial")
        self.coronal_viewer = ImageViewerWidget("coronal")
        self.sagittal_viewer = ImageViewerWidget("sagittal")
        
        # Arrange in 2x2 grid
        left_layout.addWidget(self.axial_viewer, 0, 0)
        left_layout.addWidget(self.coronal_viewer, 0, 1)
        left_layout.addWidget(self.sagittal_viewer, 1, 0)
        
        # Empty space or info panel
        info_widget = QWidget()
        info_layout = QVBoxLayout()
        
        self.position_label = QLabel("Position: (0, 0, 0)")
        self.position_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        info_layout.addWidget(self.position_label)
        
        self.value_label = QLabel("Value: 0")
        self.value_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        info_layout.addWidget(self.value_label)
        
        info_layout.addStretch()
        info_widget.setLayout(info_layout)
        left_layout.addWidget(info_widget, 1, 1)
        
        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)
        
        # Right side: 3D volume rendering
        self.volume_widget = VolumeRenderWidget()
        main_splitter.addWidget(self.volume_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([800, 400])
        
        layout.addWidget(main_splitter, 1)
        
        self.setLayout(layout)
        
        # Setup connections
        self.setup_connections()
    
    def setup_connections(self):
        """Setup signal connections giữa các viewers"""
        # Connect viewer signals (avoid recursion)
        try:
            self.axial_viewer.image_clicked.connect(
                lambda x, y, z: self.on_image_clicked("axial", x, y, z)
            )
        except:
            pass
        
        try:    
            self.coronal_viewer.image_clicked.connect(
                lambda x, y, z: self.on_image_clicked("coronal", x, y, z)
            )
        except:
            pass
            
        try:
            self.sagittal_viewer.image_clicked.connect(
                lambda x, y, z: self.on_image_clicked("sagittal", x, y, z)
            )
        except:
            pass
        
        # Window/Level synchronization
        self.axial_viewer.window_level_changed.connect(
            lambda c, w: self.on_window_level_changed("axial", c, w)
        )
        self.coronal_viewer.window_level_changed.connect(
            lambda c, w: self.on_window_level_changed("coronal", c, w)
        )
        self.sagittal_viewer.window_level_changed.connect(
            lambda c, w: self.on_window_level_changed("sagittal", c, w)
        )
    
    def load_image_data(self, image_array: np.ndarray, spacing: Tuple[float, ...] = None,
                       origin: Tuple[float, ...] = None):
        """
        Load image data vào tất cả viewers
        
        Args:
            image_array: NumPy array (3D)
            spacing: Pixel spacing (z, y, x)
            origin: Image origin
        """
        try:
            self.image_array = image_array
            self.spacing = spacing or (1.0, 1.0, 1.0)
            self.origin = origin or (0.0, 0.0, 0.0)
            
            # Set initial crosshair position to center
            center_z = image_array.shape[0] // 2
            center_y = image_array.shape[1] // 2
            center_x = image_array.shape[2] // 2
            self.crosshair_position = [center_x, center_y, center_z]
            
            # Load data vào từng viewer
            self.axial_viewer.load_image_data(image_array, spacing, origin)
            self.coronal_viewer.load_image_data(image_array, spacing, origin)
            self.sagittal_viewer.load_image_data(image_array, spacing, origin)
            
            # Load vào 3D volume renderer
            if VTK_AVAILABLE and self.volume_widget:
                # Convert to VTK format cho 3D rendering
                vtk_image = self._numpy_to_vtk_image(image_array, spacing, origin)
                self.volume_widget.load_volume_data(vtk_image)
            
            # Update position display
            self.update_position_display()
            
            logger.info(f"MPR data loaded: shape={image_array.shape}, spacing={spacing}")
            
        except Exception as e:
            logger.error(f"Error loading MPR image data: {e}")
    
    def _numpy_to_vtk_image(self, array: np.ndarray, spacing: Tuple[float, ...],
                           origin: Tuple[float, ...]):
        """Convert NumPy array to VTK image data for 3D rendering"""
        if not VTK_AVAILABLE:
            return None
        
        try:
            vtk_image = vtk.vtkImageData()
            
            # Set dimensions (VTK order: x, y, z)
            vtk_image.SetDimensions(array.shape[2], array.shape[1], array.shape[0])
            
            # Set spacing
            if len(spacing) == 3:
                vtk_image.SetSpacing(spacing[2], spacing[1], spacing[0])
            
            # Set origin
            if len(origin) == 3:
                vtk_image.SetOrigin(origin[2], origin[1], origin[0])
            
            # Convert data
            flat_array = array.flatten('F')
            
            try:
                # Try new VTK interface first
                vtk_array = vtk.numpy_interface.dataset_adapter.numpyTovtkDataArray(flat_array)
            except AttributeError:
                try:
                    # Fallback to older interface
                    from vtk.util import numpy_support
                    vtk_array = numpy_support.numpy_to_vtk(flat_array)
                except ImportError:
                    # Manual conversion as last resort
                    vtk_array = vtk.vtkFloatArray()
                    vtk_array.SetNumberOfTuples(len(flat_array))
                    for i, val in enumerate(flat_array):
                        vtk_array.SetValue(i, float(val))
            vtk_image.GetPointData().SetScalars(vtk_array)
            
            return vtk_image
            
        except Exception as e:
            logger.error(f"Error converting to VTK image: {e}")
            return None
    
    def on_image_clicked(self, orientation: str, x: float, y: float, z: float):
        """Handle click từ một viewer"""
        # TODO: Convert screen coordinates to world coordinates
        # TODO: Update crosshair position
        # TODO: Sync với other viewers
        
        self.crosshair_moved.emit(x, y, z)
    
    def on_window_level_changed(self, orientation: str, center: float, width: float):
        """Handle window/level change từ một viewer"""
        if self.sync_window_level:
            # Sync window/level đến tất cả viewers khác
            window_level = WindowLevel(center=center, width=width, name="Synced")
            
            if orientation != "axial":
                self.axial_viewer.set_window_level(window_level)
            if orientation != "coronal":
                self.coronal_viewer.set_window_level(window_level)
            if orientation != "sagittal":
                self.sagittal_viewer.set_window_level(window_level)
        
        self.window_level_changed_any.emit(center, width)
    
    def toggle_sync_window_level(self, enabled: bool):
        """Toggle window/level synchronization"""
        self.sync_window_level = enabled
        logger.info(f"Window/Level sync: {'enabled' if enabled else 'disabled'}")
    
    def update_position_display(self):
        """Cập nhật hiển thị position"""
        x, y, z = self.crosshair_position
        self.position_label.setText(f"Position: ({x}, {y}, {z})")
        
        # Get pixel value tại position hiện tại
        if self.image_array is not None:
            try:
                if (0 <= z < self.image_array.shape[0] and
                    0 <= y < self.image_array.shape[1] and
                    0 <= x < self.image_array.shape[2]):
                    value = self.image_array[z, y, x]
                    self.value_label.setText(f"Value: {value:.1f}")
                else:
                    self.value_label.setText("Value: --")
            except:
                self.value_label.setText("Value: --")
    
    def reset_all_views(self):
        """Reset tất cả views về trạng thái ban đầu"""
        self.axial_viewer.reset_view()
        self.coronal_viewer.reset_view()
        self.sagittal_viewer.reset_view()
        
        if self.volume_widget:
            self.volume_widget.reset_3d_view()
        
        logger.info("All views reset")
    
    def set_crosshair_position(self, x: int, y: int, z: int):
        """Set crosshair position và update tất cả views"""
        self.crosshair_position = [x, y, z]
        
        # Update slice numbers trong các viewers
        self.axial_viewer.on_slice_changed(z)
        self.coronal_viewer.on_slice_changed(y)
        self.sagittal_viewer.on_slice_changed(x)
        
        self.update_position_display()
    
    def export_all_screenshots(self, base_filename: str):
        """Export screenshots của tất cả views"""
        try:
            self.axial_viewer.export_screenshot(f"{base_filename}_axial.png")
            self.coronal_viewer.export_screenshot(f"{base_filename}_coronal.png")
            self.sagittal_viewer.export_screenshot(f"{base_filename}_sagittal.png")
            
            logger.info(f"All screenshots exported with base name: {base_filename}")
            
        except Exception as e:
            logger.error(f"Error exporting screenshots: {e}")
    
    def get_current_window_level(self) -> WindowLevel:
        """Lấy current window/level"""
        return self.axial_viewer.window_level
