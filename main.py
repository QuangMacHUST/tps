#!/usr/bin/env python3
"""
TPS - Treatment Planning System
Entry point chính của ứng dụng

Usage:
    python main.py
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Import application modules
from src.gui.main_window import MainWindow

# Cấu hình logging
def setup_logging():
    """Cấu hình logging cho ứng dụng"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'tps.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set up specific loggers
    logger = logging.getLogger(__name__)
    logger.info("Logging được cấu hình thành công")
    return logger


def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    required_modules = [
        'PyQt5',
        'numpy', 
        'scipy',
        'pandas',
        'pydicom',
        'SimpleITK',
        'opencv-python',
        'sqlalchemy'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules


def create_splash_screen(app):
    """Tạo splash screen"""
    # Tạo splash screen đơn giản
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.white)
    
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    
    # Add text to splash screen
    splash.setFont(QFont("Arial", 16, QFont.Bold))
    splash.showMessage(
        "TPS - Treatment Planning System\nĐang khởi tạo...", 
        Qt.AlignCenter | Qt.AlignBottom, 
        Qt.black
    )
    
    splash.show()
    app.processEvents()
    
    return splash


def main():
    """Hàm main của ứng dụng"""
    
    # Setup logging
    logger = setup_logging()
    logger.info("=== BẮT ĐẦU TPS APPLICATION ===")
    
    try:
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            print(f"CẢNH BÁO: Thiếu các dependencies: {', '.join(missing_deps)}")
            print("Vui lòng cài đặt bằng: pip install -r requirements.txt")
            
            # Vẫn tiếp tục chạy để test các tính năng có thể
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("TPS")
        app.setApplicationDisplayName("Treatment Planning System")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("TPS Development Team")
        
        # Set application style
        app.setStyle("Fusion")  # Modern look
        
        # Create splash screen
        splash = create_splash_screen(app)
        
        # Update splash message
        splash.showMessage(
            "TPS - Treatment Planning System\nĐang tải database...", 
            Qt.AlignCenter | Qt.AlignBottom, 
            Qt.black
        )
        app.processEvents()
        
        # Initialize main window
        logger.info("Khởi tạo MainWindow...")
        main_window = MainWindow()
        
        # Update splash message
        splash.showMessage(
            "TPS - Treatment Planning System\nĐang hoàn tất...", 
            Qt.AlignCenter | Qt.AlignBottom, 
            Qt.black
        )
        app.processEvents()
        
        # Close splash and show main window
        def finish_loading():
            splash.finish(main_window)
            main_window.show()
            logger.info("TPS Application đã sẵn sàng!")
        
        # Delay để người dùng có thể thấy splash screen
        QTimer.singleShot(2000, finish_loading)
        
        # Start event loop
        logger.info("Bắt đầu Qt event loop...")
        exit_code = app.exec_()
        
        logger.info(f"TPS Application kết thúc với exit code: {exit_code}")
        return exit_code
        
    except ImportError as e:
        error_msg = f"Lỗi import module: {e}\n\nVui lòng cài đặt dependencies:\npip install -r requirements.txt"
        print(error_msg)
        
        # Try to show GUI error if PyQt5 is available
        try:
            app = QApplication(sys.argv) if 'app' not in locals() else app
            QMessageBox.critical(None, "Import Error", error_msg)
        except:
            pass
        
        return 1
        
    except Exception as e:
        error_msg = f"Lỗi khởi tạo ứng dụng: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Try to show GUI error
        try:
            app = QApplication(sys.argv) if 'app' not in locals() else app
            QMessageBox.critical(None, "Application Error", error_msg)
        except:
            print(error_msg)
        
        return 1


if __name__ == "__main__":
    # Ensure proper exit
    sys.exit(main())
