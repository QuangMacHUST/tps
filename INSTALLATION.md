# Hướng Dẫn Cài Đặt và Chạy TPS

## Yêu Cầu Hệ Thống

- **Python**: 3.8 hoặc cao hơn
- **OS**: Windows 10+, Linux Ubuntu 18.04+, macOS 10.14+
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB+
- **Dung lượng**: 2GB trống

## Cài Đặt Nhanh

### Bước 1: Clone Repository
```bash
git clone https://github.com/yourusername/tps.git
cd tps
```

### Bước 2: Tạo Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Bước 3: Cài Đặt Dependencies

#### Cài Đặt Cơ Bản (Tối Thiểu)
```bash
pip install PyQt5 numpy pandas sqlalchemy
```

#### Cài Đặt Đầy Đủ (Khuyến Nghị)
```bash
pip install -r requirements.txt
```

**Lưu ý**: Nếu gặp lỗi khi cài đặt, hãy thử:
```bash
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

### Bước 4: Khởi Tạo Database
```bash
python scripts/init_database.py
```

### Bước 5: Chạy Ứng Dụng
```bash
python main.py
```

## Kiểm Tra Cài Đặt

### Test Nhanh
```bash
python test_simple.py
```

### Test Chi Tiết (Optional)
```bash
python scripts/run_tests.py
```

## Cấu Trúc Dự Án Sau Khi Cài Đặt

```
tps/
├── main.py                    # Entry point chính
├── requirements.txt           # Dependencies
├── setup.py                   # Setup script
├── test_simple.py             # Test đơn giản
│
├── src/                       # Source code
│   ├── core/                  # Modules cốt lõi
│   │   ├── patient_manager.py # Quản lý bệnh nhân ✓
│   │   ├── dicom_handler.py   # DICOM I/O ✓  
│   │   └── image_processor.py # Xử lý ảnh ✓
│   │
│   └── gui/                   # GUI components
│       ├── main_window.py     # Cửa sổ chính ✓
│       └── patient_browser.py # Trình duyệt BN ✓
│
├── data/                      # Dữ liệu
│   ├── patient_database/      # Database bệnh nhân ✓
│   └── beam_data/             # Truebeam data ✓
│
├── scripts/                   # Utility scripts
│   ├── init_database.py       # Khởi tạo DB ✓
│   └── run_tests.py           # Test runner ✓
│
└── logs/                      # Log files
```

## Tính Năng Hiện Có

### ✅ Hoàn Thành
- **Quản lý bệnh nhân**: CRUD operations, search, filter
- **DICOM I/O**: Import/export, metadata parsing
- **Database**: SQLite với full backup/restore
- **GUI**: Patient browser với modern interface
- **Image Processing**: Basic operations, window/level
- **Export**: CSV export, database backup

### 🔄 Đang Phát Triển
- Image viewer và visualization
- Contouring tools
- Planning workspace  
- Dose calculation algorithms
- Optimization engines

## Troubleshooting

### Lỗi Import PyQt5
```bash
# Windows
pip install PyQt5
# hoặc
pip install PySide2

# Linux (Ubuntu/Debian)
sudo apt-get install python3-pyqt5

# macOS
brew install pyqt5
```

### Lỗi Cài Đặt SimpleITK
```bash
pip install --upgrade pip
pip install SimpleITK
```

### Lỗi Database Permission
```bash
# Tạo thư mục data nếu chưa có
mkdir -p data/patient_database

# Set permissions (Linux/Mac)
chmod 755 data/patient_database
```

### Ứng Dụng Không Khởi Động
1. Kiểm tra Python version: `python --version`
2. Kiểm tra PyQt5: `python -c "import PyQt5; print('OK')"`
3. Chạy test: `python test_simple.py`
4. Check logs trong thư mục `logs/`

## Cấu Hình Tùy Chọn

### Machine Configuration
Chỉnh sửa file `config/machine_config.json`:
```json
{
  "machine_name": "Your_Machine_Name",
  "energies": ["6MV", "10MV", "15MV"],
  "database_path": "custom/path/to/patients.db"
}
```

### Algorithm Settings  
Chỉnh sửa file `config/algorithm_config.json`:
```json
{
  "default_algorithm": "PBC",
  "grid_size": 2.0,
  "auto_backup": true
}
```

## Phát Triển

### Cài Đặt Development Dependencies
```bash
pip install -r requirements.txt
pip install pytest black pylint
```

### Chạy Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ --line-length 100
```

### Linting
```bash
pylint src/
```

## Hỗ Trợ

- **Issues**: [GitHub Issues](https://github.com/yourusername/tps/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/tps/wiki)
- **Email**: tps-support@example.com

## Cập Nhật

### Cập Nhật Code
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Backup Trước Khi Cập Nhật
```bash
python -c "from src.core.patient_manager import PatientManager; pm = PatientManager(); pm.backup_database('backup_before_update.db')"
```

---

**Lưu ý An Toàn**: Đây là phần mềm nghiên cứu. Không sử dụng cho mục đích lâm sàng mà không có validation và certification phù hợp.
