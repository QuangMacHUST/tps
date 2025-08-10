#!/usr/bin/env python3
"""
Test visualization components cho TPS
"""

import sys
import os
from pathlib import Path
import logging
import numpy as np

# Add src to Python path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vtk_import():
    """Test VTK import"""
    logger.info("Testing VTK import...")
    
    try:
        import vtk
        logger.info(f"✓ VTK version: {vtk.vtkVersion.GetVTKVersion()}")
        return True
    except ImportError as e:
        logger.error(f"✗ VTK import failed: {e}")
        logger.info("Install VTK: pip install vtk")
        return False

def test_gui_components():
    """Test GUI components"""
    logger.info("Testing GUI components...")
    
    try:
        from src.gui.image_viewer_widget import ImageViewerWidget
        logger.info("✓ ImageViewerWidget import: OK")
        
        from src.gui.mpr_viewer_widget import MPRViewerWidget
        logger.info("✓ MPRViewerWidget import: OK")
        
        from src.gui.advanced_controls_widget import AdvancedControlsWidget
        logger.info("✓ AdvancedControlsWidget import: OK")
        
        from src.gui.series_navigator_widget import SeriesNavigatorWidget
        logger.info("✓ SeriesNavigatorWidget import: OK")
        
        from src.gui.image_workspace import ImageWorkspace
        logger.info("✓ ImageWorkspace import: OK")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ GUI component import failed: {e}")
        return False

def test_image_viewer_widget():
    """Test ImageViewerWidget creation"""
    logger.info("Testing ImageViewerWidget creation...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from src.gui.image_viewer_widget import ImageViewerWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test tạo widget
        viewer = ImageViewerWidget("axial")
        logger.info("✓ ImageViewerWidget creation: OK")
        
        # Test load test data
        test_data = np.random.randint(0, 1000, (50, 256, 256), dtype=np.int16)
        viewer.load_image_data(test_data, spacing=(1.0, 1.0, 1.0))
        logger.info("✓ Test data loading: OK")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ImageViewerWidget test failed: {e}")
        return False

def test_mpr_viewer_widget():
    """Test MPRViewerWidget creation"""
    logger.info("Testing MPRViewerWidget creation...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from src.gui.mpr_viewer_widget import MPRViewerWidget
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test tạo widget
        mpr_viewer = MPRViewerWidget()
        logger.info("✓ MPRViewerWidget creation: OK")
        
        # Test load test data
        test_data = np.random.randint(0, 1000, (50, 256, 256), dtype=np.int16)
        mpr_viewer.load_image_data(test_data, spacing=(1.0, 1.0, 1.0))
        logger.info("✓ MPR test data loading: OK")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ MPRViewerWidget test failed: {e}")
        return False

def test_image_workspace():
    """Test ImageWorkspace creation"""
    logger.info("Testing ImageWorkspace creation...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from src.gui.image_workspace import ImageWorkspace
        from src.core.patient_manager import PatientManager
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test tạo workspace
        pm = PatientManager(db_path="test_viz.db")
        workspace = ImageWorkspace(pm)
        logger.info("✓ ImageWorkspace creation: OK")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ ImageWorkspace test failed: {e}")
        return False

def test_full_gui():
    """Test full GUI với hiển thị"""
    logger.info("Testing full GUI display...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from src.gui.image_workspace import ImageWorkspace
        from src.core.patient_manager import PatientManager
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Tạo workspace
        pm = PatientManager(db_path="test_viz.db")
        workspace = ImageWorkspace(pm)
        
        # Show workspace (không exec để test không block)
        workspace.show()
        logger.info("✓ GUI display: OK")
        
        # Process events một chút
        app.processEvents()
        
        # Close
        workspace.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Full GUI test failed: {e}")
        return False

def cleanup():
    """Cleanup test files"""
    test_files = ["test_viz.db"]
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                logger.info(f"Cleaned up: {file}")
            except:
                pass

def main():
    """Main test function"""
    logger.info("=== TPS VISUALIZATION TESTS ===")
    
    tests = [
        ("VTK Import", test_vtk_import),
        ("GUI Components Import", test_gui_components),
        ("ImageViewerWidget", test_image_viewer_widget),
        ("MPRViewerWidget", test_mpr_viewer_widget),
        ("ImageWorkspace", test_image_workspace),
        ("Full GUI Display", test_full_gui)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"{test_name}: PASSED ✓")
            else:
                failed += 1
                logger.error(f"{test_name}: FAILED ✗")
        except Exception as e:
            failed += 1
            logger.error(f"{test_name}: ERROR - {e}")
    
    # Cleanup
    cleanup()
    
    logger.info(f"\n=== VISUALIZATION TEST RESULTS ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All visualization tests passed!")
        logger.info("You can now run the Image Workspace with:")
        logger.info("python main.py")
    else:
        logger.error(f"❌ {failed} tests failed")
        logger.info("Please check the error messages above")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
