"""
Module Image Viewer Widget - Trình xem ảnh y tế với VTK

Chức năng:
- Hiển thị ảnh DICOM với VTK
- Window/Level controls
- Zoom, Pan, Rotate operations
- Measurements và annotations
- Mouse interactions
"""

import logging
from typing import Optional, Tuple, List, Any
import numpy as np

try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    # Fallback imports for basic functionality
    QVTKRenderWindowInteractor = object

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QSpinBox, QPushButton, QGroupBox,
    QGridLayout, QCheckBox, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor

from ..core.image_processor import ImageProcessor, WindowLevel

# Cấu hình logging
logger = logging.getLogger(__name__)


class ImageViewerWidget(QWidget):
    """
    Widget trình xem ảnh y tế sử dụng VTK
    Tương đương với image viewer trong Eclipse TPS
    """
    
    # Signals
    image_clicked = pyqtSignal(float, float, float)  # x, y, z coordinates
    window_level_changed = pyqtSignal(float, float)  # center, width
    slice_changed = pyqtSignal(int)  # slice index
    zoom_changed = pyqtSignal(float)  # zoom factor
    
    def __init__(self, orientation: str = "axial", parent=None):
        """
        Khởi tạo Image Viewer
        
        Args:
            orientation: "axial", "coronal", "sagittal"
            parent: Parent widget
        """
        super().__init__(parent)
        
        if not VTK_AVAILABLE:
            logger.error("VTK not available! Please install vtk: pip install vtk")
            self._setup_fallback_ui()
            return
        
        self.orientation = orientation
        self.image_data = None
        self.current_slice = 0
        self.window_level = WindowLevel(center=127, width=255, name="Default")
        self.zoom_factor = 1.0
        
        # VTK components
        self.vtk_widget = None
        self.renderer = None
        self.render_window = None
        self.interactor = None
        self.image_actor = None
        self.image_mapper = None
        
        # Image processor
        self.image_processor = ImageProcessor()
        
        self.setup_ui()
        self.setup_vtk()
        
        logger.info(f"ImageViewerWidget initialized for {orientation} view")
    
    def _setup_fallback_ui(self):
        """Setup fallback UI khi VTK không available"""
        layout = QVBoxLayout()
        
        warning_label = QLabel("⚠️ VTK Library không khả dụng")
        warning_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        install_label = QLabel("Vui lòng cài đặt: pip install vtk>=9.2.0")
        install_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(install_label)
        
        self.setLayout(layout)
        return
    
    def setup_ui(self):
        """Thiết lập giao diện"""
        layout = QVBoxLayout()
        
        # Header với title và controls
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(f"{self.orientation.title()} View")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Quick controls
        self.slice_label = QLabel("Slice: 0/0")
        header_layout.addWidget(self.slice_label)
        
        self.window_label = QLabel("W/L: 255/127")
        header_layout.addWidget(self.window_label)
        
        self.zoom_label = QLabel("Zoom: 100%")
        header_layout.addWidget(self.zoom_label)
        
        layout.addLayout(header_layout)
        
        # Main VTK widget container
        self.vtk_container = QFrame()
        self.vtk_container.setFrameStyle(QFrame.StyledPanel)
        self.vtk_container.setMinimumSize(400, 400)
        
        # VTK widget sẽ được thêm vào container này
        self.vtk_layout = QVBoxLayout()
        self.vtk_container.setLayout(self.vtk_layout)
        
        layout.addWidget(self.vtk_container, 1)  # Stretch để chiếm toàn bộ space
        
        # Controls panel
        controls_group = QGroupBox("Controls")
        controls_layout = QGridLayout()
        
        # Slice control
        controls_layout.addWidget(QLabel("Slice:"), 0, 0)
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.valueChanged.connect(self.on_slice_changed)
        controls_layout.addWidget(self.slice_slider, 0, 1)
        
        self.slice_spinbox = QSpinBox()
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(0)
        self.slice_spinbox.valueChanged.connect(self.on_slice_changed)
        controls_layout.addWidget(self.slice_spinbox, 0, 2)
        
        # Window/Level controls
        controls_layout.addWidget(QLabel("Window:"), 1, 0)
        self.window_slider = QSlider(Qt.Horizontal)
        self.window_slider.setMinimum(1)
        self.window_slider.setMaximum(4000)
        self.window_slider.setValue(int(self.window_level.width))
        self.window_slider.valueChanged.connect(self.on_window_changed)
        controls_layout.addWidget(self.window_slider, 1, 1)
        
        self.window_spinbox = QSpinBox()
        self.window_spinbox.setMinimum(1)
        self.window_spinbox.setMaximum(4000)
        self.window_spinbox.setValue(int(self.window_level.width))
        self.window_spinbox.valueChanged.connect(self.on_window_changed)
        controls_layout.addWidget(self.window_spinbox, 1, 2)
        
        controls_layout.addWidget(QLabel("Level:"), 2, 0)
        self.level_slider = QSlider(Qt.Horizontal)
        self.level_slider.setMinimum(-1000)
        self.level_slider.setMaximum(3000)
        self.level_slider.setValue(int(self.window_level.center))
        self.level_slider.valueChanged.connect(self.on_level_changed)
        controls_layout.addWidget(self.level_slider, 2, 1)
        
        self.level_spinbox = QSpinBox()
        self.level_spinbox.setMinimum(-1000)
        self.level_spinbox.setMaximum(3000)
        self.level_spinbox.setValue(int(self.window_level.center))
        self.level_spinbox.valueChanged.connect(self.on_level_changed)
        controls_layout.addWidget(self.level_spinbox, 2, 2)
        
        # Preset buttons
        preset_layout = QHBoxLayout()
        
        presets = [
            ("Bone", WindowLevel(400, 1500, "Bone")),
            ("Soft Tissue", WindowLevel(50, 350, "Soft Tissue")),
            ("Lung", WindowLevel(-600, 1600, "Lung")),
            ("Brain", WindowLevel(40, 80, "Brain"))
        ]
        
        for name, wl in presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, w=wl: self.set_window_level(w))
            preset_layout.addWidget(btn)
        
        controls_layout.addLayout(preset_layout, 3, 0, 1, 3)
        
        # Tools
        tools_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.clicked.connect(self.reset_view)
        tools_layout.addWidget(self.reset_btn)
        
        self.fit_btn = QPushButton("Fit to Window")
        self.fit_btn.clicked.connect(self.fit_to_window)
        tools_layout.addWidget(self.fit_btn)
        
        self.measurements_check = QCheckBox("Show Measurements")
        tools_layout.addWidget(self.measurements_check)
        
        controls_layout.addLayout(tools_layout, 4, 0, 1, 3)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        self.setLayout(layout)
    
    def setup_vtk(self):
        """Thiết lập VTK components"""
        if not VTK_AVAILABLE:
            return
        
        try:
            # Create VTK widget
            self.vtk_widget = QVTKRenderWindowInteractor(self.vtk_container)
            self.vtk_layout.addWidget(self.vtk_widget)
            
            # Get render window and renderer
            self.render_window = self.vtk_widget.GetRenderWindow()
            self.renderer = vtk.vtkRenderer()
            self.renderer.SetBackground(0, 0, 0)  # Black background
            self.render_window.AddRenderer(self.renderer)
            
            # Get interactor
            self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
            
            # Setup interactor style cho medical imaging
            style = vtk.vtkInteractorStyleImage()
            self.interactor.SetInteractorStyle(style)
            
            # Setup camera orientation theo view
            self.setup_camera_orientation()
            
            # Add mouse/keyboard event handling
            self.setup_interactions()
            
            logger.info("VTK setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up VTK: {e}")
    
    def setup_camera_orientation(self):
        """Setup camera orientation theo view plane"""
        if not self.renderer:
            return
        
        camera = self.renderer.GetActiveCamera()
        
        if self.orientation == "axial":
            # Axial view (top-down)
            camera.SetPosition(0, 0, 1)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 1, 0)
        elif self.orientation == "coronal":
            # Coronal view (front-back)
            camera.SetPosition(0, 1, 0)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
        elif self.orientation == "sagittal":
            # Sagittal view (left-right)
            camera.SetPosition(1, 0, 0)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
        
        camera.ParallelProjectionOn()  # Orthographic projection cho medical images
    
    def setup_interactions(self):
        """Setup mouse và keyboard interactions"""
        if not self.interactor:
            return
        
        # Add observer cho mouse events
        self.interactor.AddObserver("LeftButtonPressEvent", self.on_left_button_press)
        self.interactor.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.interactor.AddObserver("MouseWheelForwardEvent", self.on_mouse_wheel_forward)
        self.interactor.AddObserver("MouseWheelBackwardEvent", self.on_mouse_wheel_backward)
    
    def load_image_data(self, image_array: np.ndarray, spacing: Tuple[float, ...] = None, 
                       origin: Tuple[float, ...] = None):
        """
        Load image data vào viewer
        
        Args:
            image_array: NumPy array (3D)
            spacing: Pixel spacing
            origin: Image origin
        """
        if not VTK_AVAILABLE:
            logger.error("Cannot load image data - VTK not available")
            return
        
        try:
            # Convert NumPy array to VTK image
            self.image_data = self._numpy_to_vtk_image(image_array, spacing, origin)
            
            # Update slice controls
            dims = self.image_data.GetDimensions()
            
            if self.orientation == "axial":
                max_slice = dims[2] - 1
            elif self.orientation == "coronal":
                max_slice = dims[1] - 1
            else:  # sagittal
                max_slice = dims[0] - 1
            
            self.slice_slider.setMaximum(max_slice)
            self.slice_spinbox.setMaximum(max_slice)
            
            # Set initial slice to middle
            initial_slice = max_slice // 2
            self.current_slice = initial_slice
            self.slice_slider.setValue(initial_slice)
            self.slice_spinbox.setValue(initial_slice)
            
            # Create image mapper và actor
            self.create_image_mapper()
            
            # Update display
            self.update_display()
            
            # Auto window/level
            self.auto_window_level()
            
            # Update labels
            self.update_labels()
            
            logger.info(f"Loaded image data: {dims}, orientation: {self.orientation}")
            
        except Exception as e:
            logger.error(f"Error loading image data: {e}")
    
    def _numpy_to_vtk_image(self, array: np.ndarray, spacing: Tuple[float, ...] = None,
                           origin: Tuple[float, ...] = None) -> vtk.vtkImageData:
        """Convert NumPy array to VTK image data"""
        # Create VTK image data
        vtk_image = vtk.vtkImageData()
        
        # Set dimensions (VTK uses x,y,z order)
        if array.ndim == 3:
            vtk_image.SetDimensions(array.shape[2], array.shape[1], array.shape[0])
        else:
            raise ValueError("Array must be 3D")
        
        # Set spacing
        if spacing:
            if len(spacing) == 3:
                vtk_image.SetSpacing(spacing[2], spacing[1], spacing[0])  # Reverse order
            else:
                vtk_image.SetSpacing(1.0, 1.0, 1.0)
        else:
            vtk_image.SetSpacing(1.0, 1.0, 1.0)
        
        # Set origin
        if origin:
            if len(origin) == 3:
                vtk_image.SetOrigin(origin[2], origin[1], origin[0])  # Reverse order
            else:
                vtk_image.SetOrigin(0.0, 0.0, 0.0)
        else:
            vtk_image.SetOrigin(0.0, 0.0, 0.0)
        
        # Convert array to VTK format
        flat_array = array.flatten('F')  # Fortran order cho VTK
        
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
        
        # Set scalar data
        vtk_image.GetPointData().SetScalars(vtk_array)
        
        return vtk_image
    
    def create_image_mapper(self):
        """Tạo image mapper cho slice display"""
        if not self.image_data:
            return
        
        # Create image slice mapper
        self.image_mapper = vtk.vtkImageSliceMapper()
        self.image_mapper.SetInputData(self.image_data)
        
        # Set slice orientation
        if self.orientation == "axial":
            self.image_mapper.SetOrientationToZ()
        elif self.orientation == "coronal":
            self.image_mapper.SetOrientationToY()
        else:  # sagittal
            self.image_mapper.SetOrientationToX()
        
        # Create image actor
        self.image_actor = vtk.vtkImageSlice()
        self.image_actor.SetMapper(self.image_mapper)
        
        # Set image properties
        image_property = self.image_actor.GetProperty()
        image_property.SetInterpolationTypeToLinear()
        
        # Add to renderer
        if self.renderer:
            self.renderer.RemoveAllViewProps()  # Clear previous actors
            self.renderer.AddViewProp(self.image_actor)
    
    def update_display(self):
        """Cập nhật display với current slice và window/level"""
        if not self.image_mapper or not self.image_actor:
            return
        
        try:
            # Update slice number
            self.image_mapper.SetSliceNumber(self.current_slice)
            
            # Update window/level
            image_property = self.image_actor.GetProperty()
            image_property.SetColorWindow(self.window_level.width)
            image_property.SetColorLevel(self.window_level.center)
            
            # Render
            if self.render_window:
                self.render_window.Render()
                
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def auto_window_level(self):
        """Tự động tính window/level từ image data"""
        if not self.image_data:
            return
        
        try:
            # Get scalar range
            scalar_range = self.image_data.GetScalarRange()
            min_val, max_val = scalar_range
            
            # Calculate auto window/level
            center = (min_val + max_val) / 2
            width = max_val - min_val
            
            # Set reasonable limits
            if width > 4000:
                width = 4000
            if width < 1:
                width = 1
            
            self.window_level = WindowLevel(center=center, width=width, name="Auto")
            
            # Update controls
            self.window_slider.setValue(int(width))
            self.window_spinbox.setValue(int(width))
            self.level_slider.setValue(int(center))
            self.level_spinbox.setValue(int(center))
            
            # Update display
            self.update_display()
            
            logger.info(f"Auto window/level: W={width:.0f}, L={center:.0f}")
            
        except Exception as e:
            logger.error(f"Error in auto window/level: {e}")
    
    def set_window_level(self, window_level: WindowLevel):
        """Set window/level preset"""
        self.window_level = window_level
        
        # Update controls
        self.window_slider.setValue(int(window_level.width))
        self.window_spinbox.setValue(int(window_level.width))
        self.level_slider.setValue(int(window_level.center))
        self.level_spinbox.setValue(int(window_level.center))
        
        # Update display
        self.update_display()
        
        # Emit signal
        self.window_level_changed.emit(window_level.center, window_level.width)
        
        self.update_labels()
    
    def on_slice_changed(self, value: int):
        """Handle slice change"""
        if self.current_slice != value:
            self.current_slice = value
            
            # Sync slider và spinbox
            if self.sender() == self.slice_slider:
                self.slice_spinbox.setValue(value)
            else:
                self.slice_slider.setValue(value)
            
            # Update display
            self.update_display()
            
            # Update label
            self.update_labels()
            
            # Emit signal
            self.slice_changed.emit(value)
    
    def on_window_changed(self, value: int):
        """Handle window width change"""
        self.window_level.width = value
        
        # Sync slider và spinbox
        if self.sender() == self.window_slider:
            self.window_spinbox.setValue(value)
        else:
            self.window_slider.setValue(value)
        
        # Update display
        self.update_display()
        
        # Update label
        self.update_labels()
        
        # Emit signal
        self.window_level_changed.emit(self.window_level.center, self.window_level.width)
    
    def on_level_changed(self, value: int):
        """Handle window level change"""
        self.window_level.center = value
        
        # Sync slider và spinbox
        if self.sender() == self.level_slider:
            self.level_spinbox.setValue(value)
        else:
            self.level_slider.setValue(value)
        
        # Update display
        self.update_display()
        
        # Update label
        self.update_labels()
        
        # Emit signal
        self.window_level_changed.emit(self.window_level.center, self.window_level.width)
    
    def update_labels(self):
        """Cập nhật text labels"""
        if self.image_data:
            dims = self.image_data.GetDimensions()
            if self.orientation == "axial":
                max_slice = dims[2] - 1
            elif self.orientation == "coronal":
                max_slice = dims[1] - 1
            else:
                max_slice = dims[0] - 1
            
            self.slice_label.setText(f"Slice: {self.current_slice}/{max_slice}")
        
        self.window_label.setText(f"W/L: {int(self.window_level.width)}/{int(self.window_level.center)}")
        self.zoom_label.setText(f"Zoom: {int(self.zoom_factor * 100)}%")
    
    def reset_view(self):
        """Reset view về trạng thái ban đầu"""
        if self.renderer:
            self.renderer.ResetCamera()
            self.zoom_factor = 1.0
            self.update_display()
            self.update_labels()
    
    def fit_to_window(self):
        """Fit image to window size"""
        if self.renderer:
            self.renderer.ResetCamera()
            self.zoom_factor = 1.0
            self.update_display()
            self.update_labels()
    
    def on_left_button_press(self, obj, event):
        """Handle left mouse button press"""
        if not self.interactor:
            return
        
        # Get mouse position
        x, y = self.interactor.GetEventPosition()
        
        # Convert to world coordinates
        # TODO: Implement coordinate conversion
        
        # Emit signal với coordinates
        self.image_clicked.emit(float(x), float(y), float(self.current_slice))
    
    def on_mouse_move(self, obj, event):
        """Handle mouse move for window/level adjustment"""
        pass  # TODO: Implement mouse window/level
    
    def on_mouse_wheel_forward(self, obj, event):
        """Handle mouse wheel forward (next slice)"""
        if self.current_slice < self.slice_slider.maximum():
            self.on_slice_changed(self.current_slice + 1)
    
    def on_mouse_wheel_backward(self, obj, event):
        """Handle mouse wheel backward (previous slice)"""
        if self.current_slice > 0:
            self.on_slice_changed(self.current_slice - 1)
    
    def get_current_slice_image(self) -> Optional[np.ndarray]:
        """Lấy current slice dưới dạng numpy array"""
        if not self.image_data:
            return None
        
        try:
            # Extract current slice
            extract = vtk.vtkImageSlice()
            # TODO: Implement slice extraction
            
            return None  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting current slice: {e}")
            return None
    
    def export_screenshot(self, filename: str):
        """Export screenshot của current view"""
        if not self.render_window:
            return False
        
        try:
            # Create window to image filter
            w2if = vtk.vtkWindowToImageFilter()
            w2if.SetInput(self.render_window)
            w2if.Update()
            
            # Create PNG writer
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(filename)
            writer.SetInputConnection(w2if.GetOutputPort())
            writer.Write()
            
            logger.info(f"Screenshot exported: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting screenshot: {e}")
            return False
