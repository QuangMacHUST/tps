"""
Module GUI - Giao diện người dùng

Bao gồm:
- Main window
- Patient browser
- Image viewer và MPR
- Advanced controls
- Series navigator
- Image workspace
"""

from .main_window import MainWindow
from .patient_browser import PatientBrowser
from .image_viewer_widget import ImageViewerWidget
from .mpr_viewer_widget import MPRViewerWidget
from .advanced_controls_widget import AdvancedControlsWidget
from .series_navigator_widget import SeriesNavigatorWidget
from .image_workspace import ImageWorkspace

__all__ = [
    'MainWindow',
    'PatientBrowser',
    'ImageViewerWidget',
    'MPRViewerWidget', 
    'AdvancedControlsWidget',
    'SeriesNavigatorWidget',
    'ImageWorkspace'
]
