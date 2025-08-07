"""
Module GUI - Giao diện người dùng

Bao gồm:
- Main window
- Patient browser
- Image viewer widget
- Contouring tools
- Planning workspace
- Dose analysis panel
- Optimization panel
- Report generator
- Settings dialog
"""

from .main_window import MainWindow
from .patient_browser import PatientBrowser

__all__ = [
    'MainWindow',
    'PatientBrowser'
]
