# Hệ Thống Lập Kế Hoạch Xạ Trị (TPS) - Treatment Planning System

## Tổng Quan

Hệ thống TPS là một giải pháp toàn diện cho lập kế hoạch xạ trị với giao diện người dùng hiện đại, tương đương với Eclipse của Varian. Hệ thống hỗ trợ đầy đủ quy trình từ quản lý dữ liệu bệnh nhân, contouring, planning, tính toán liều, tối ưu hóa đến trực quan hóa và đánh giá kế hoạch điều trị.

## Cấu Trúc Dự Án

```
tps/
├── README.md
├── requirements.txt
├── setup.py
├── main.py
│
├── data/
│   ├── beam_data/                      # Dữ liệu commissioning máy gia tốc
│   │   └── Truebeam representative Beam Data for eclipse/
│   │       ├── *.xlsx                  # Dữ liệu beam các năng lượng
│   │       └── W2CAD/                  # Dữ liệu commissioning chi tiết
│   ├── patient_database/               # Cơ sở dữ liệu bệnh nhân
│   ├── templates/                      # Templates cho protocols, structures
│   └── calibration/                    # Dữ liệu hiệu chuẩn
│
├── src/
│   ├── core/                          # Module cốt lõi
│   │   ├── __init__.py
│   │   ├── patient_manager.py         # Quản lý dữ liệu bệnh nhân
│   │   ├── dicom_handler.py           # Xử lý DICOM I/O
│   │   ├── image_processor.py         # Xử lý hình ảnh
│   │   ├── structure_handler.py       # Xử lý structures/ROI
│   │   ├── beam_geometry.py           # Hình học beam
│   │   └── coordinate_system.py       # Hệ tọa độ IEC 61217
│   │
│   ├── contouring/                    # Module Contouring
│   │   ├── __init__.py
│   │   ├── manual_tools.py            # Công cụ vẽ thủ công
│   │   ├── auto_segmentation.py       # Phân đoạn tự động
│   │   ├── interpolation.py           # Nội suy giữa các slice
│   │   ├── editing_tools.py           # Công cụ chỉnh sửa ROI
│   │   ├── atlas_based.py             # Segmentation dựa trên atlas
│   │   └── quality_control.py         # Kiểm soát chất lượng contouring
│   │
│   ├── planning/                      # Module Planning
│   │   ├── __init__.py
│   │   ├── beam_setup.py              # Thiết lập beam
│   │   ├── field_geometry.py          # Hình học field
│   │   ├── mlc_handler.py             # Xử lý Multi-Leaf Collimator
│   │   ├── wedge_handler.py           # Xử lý wedge filters
│   │   ├── plan_validation.py         # Kiểm tra tính khả thi
│   │   └── plan_templates.py          # Templates kế hoạch điều trị
│   │
│   ├── dose_calculation/              # Module Tính Liều
│   │   ├── __init__.py
│   │   ├── algorithms/                # Thuật toán tính liều
│   │   │   ├── pencil_beam.py         # Pencil Beam Convolution
│   │   │   ├── collapsed_cone.py      # Collapsed Cone Convolution
│   │   │   ├── anisotropic_analytical.py  # AAA Algorithm
│   │   │   ├── acuros_xb.py          # Acuros XB (Grid-based Boltzmann)
│   │   │   └── fast_dose_calc.py     # Thuật toán tính liều nhanh
│   │   ├── beam_modeling.py           # Mô hình hóa beam
│   │   ├── heterogeneity_correction.py # Hiệu chỉnh độ không đồng nhất
│   │   ├── dose_grid.py               # Lưới tính liều
│   │   └── dose_metrics.py            # Tính toán các chỉ số liều
│   │
│   ├── optimization/                  # Module Tối Ưu Hóa
│   │   ├── __init__.py
│   │   ├── objectives.py              # Hàm mục tiêu
│   │   ├── constraints.py             # Ràng buộc
│   │   ├── optimizer_engines.py       # Các engine tối ưu
│   │   ├── imrt_optimizer.py          # Tối ưu IMRT
│   │   ├── vmat_optimizer.py          # Tối ưu VMAT
│   │   └── adaptive_planning.py       # Planning thích ứng
│   │
│   ├── visualization/                 # Module Trực Quan Hóa
│   │   ├── __init__.py
│   │   ├── image_viewer.py            # Hiển thị hình ảnh CT/MRI
│   │   ├── dose_display.py            # Hiển thị phân bố liều
│   │   ├── dvh_analysis.py            # Phân tích DVH
│   │   ├── isodose_lines.py           # Đường isodose
│   │   ├── 3d_viewer.py               # Viewer 3D
│   │   ├── beam_eye_view.py           # Beam's Eye View
│   │   └── plan_comparison.py         # So sánh kế hoạch
│   │
│   ├── qa/                           # Module Quality Assurance
│   │   ├── __init__.py
│   │   ├── plan_check.py             # Kiểm tra kế hoạch
│   │   ├── dose_verification.py      # Xác minh liều
│   │   ├── machine_qa.py             # QA máy móc
│   │   └── statistical_analysis.py  # Phân tích thống kê
│   │
│   ├── utilities/                    # Tiện ích
│   │   ├── __init__.py
│   │   ├── math_utils.py             # Hàm toán học
│   │   ├── geometry_utils.py         # Tiện ích hình học
│   │   ├── file_utils.py             # Xử lý file
│   │   ├── logging_config.py         # Cấu hình logging
│   │   └── config_manager.py         # Quản lý cấu hình
│   │
│   └── gui/                          # Giao Diện Người Dùng
│       ├── __init__.py
│       ├── main_window.py            # Cửa sổ chính
│       ├── patient_browser.py        # Trình duyệt bệnh nhân
│       ├── image_viewer_widget.py    # Widget hiển thị hình ảnh
│       ├── contouring_tools.py       # Công cụ contouring
│       ├── planning_workspace.py     # Workspace planning
│       ├── dose_analysis_panel.py    # Panel phân tích liều
│       ├── optimization_panel.py     # Panel tối ưu hóa
│       ├── report_generator.py       # Tạo báo cáo
│       └── settings_dialog.py        # Dialog cài đặt
│
├── tests/                            # Test Suite
│   ├── unit_tests/
│   ├── integration_tests/
│   └── performance_tests/
│
├── docs/                             # Tài liệu
│   ├── user_manual/
│   ├── technical_specs/
│   └── api_reference/
│
└── config/                           # File cấu hình
    ├── machine_config.json
    ├── algorithm_config.json
    └── user_preferences.json
```

## Tính Năng Chính

### 1. Quản Lý Dữ Liệu Bệnh Nhân
- **DICOM Import/Export**: Hỗ trợ đầy đủ các định dạng DICOM (CT, MRI, PET, RT-Struct, RT-Plan, RT-Dose)
- **Database Management**: Cơ sở dữ liệu bệnh nhân với tìm kiếm và lọc mạnh mẽ
- **Multi-format Support**: Xuất nhập ảnh đa định dạng (DICOM, NIfTI, Analyze, etc.)
- **Data Anonymization**: Ẩn danh hóa dữ liệu bệnh nhân
- **Backup & Recovery**: Sao lưu và phục hồi dữ liệu

### 2. Contouring (Vẽ Cấu Trúc)
- **Manual Contouring Tools**:
  - Brush Tool với size và opacity điều chỉnh được
  - Polygon Tool cho vẽ chính xác
  - Circle/Ellipse Tool
  - Freehand Drawing
  - Smart Scissors (Intelligent Edge Detection)
  
- **Editing Tools**:
  - Boolean Operations (Union, Intersection, Subtraction)
  - Morphological Operations (Erosion, Dilation, Opening, Closing)
  - Smooth & Interpolate
  - Copy & Paste between slices
  - Undo/Redo với unlimited history
  
- **Quality Control**:
  - Volume Statistics
  - Contour Validation
  - Inter-observer Variability Analysis

### 3. Planning (Lập Kế Hoạch)
- **Beam Setup**:
  - Multi-energy Support (4MV, 6MV, 8MV, 10MV, 15MV, 6FFF, 10FFF)
  - Electron Beam Support (6-22 MeV)
  - Custom Beam Arrangements
  - Isocenter Planning
  
- **Field Shaping**:
  - Multi-Leaf Collimator (MLC) Support
  - Wedge Filter Integration
  - Custom Blocks
  - Aperture Optimization
  
- **Treatment Techniques**:
  - 3D-CRT (3D Conformal Radiation Therapy)
  - IMRT (Intensity Modulated Radiation Therapy)
  - VMAT (Volumetric Modulated Arc Therapy)
  - SRS/SBRT Planning
  
- **Plan Validation**:
  - Machine Constraints Check
  - Collision Detection
  - Dose Rate Verification
  - MU Calculation Verification

### 4. Dose Calculation (Tính Toán Liều)
- **Algorithms**:
  - **Pencil Beam Convolution (PBC)**: Nhanh, phù hợp cho homogeneous media
  - **Collapsed Cone Convolution (CCC)**: Cân bằng tốc độ và độ chính xác
  - **Anisotropic Analytical Algorithm (AAA)**: Chính xác cao cho heterogeneous media
  - **Acuros XB**: Grid-based Boltzmann solver, chính xác nhất
  - **Fast Dose Calculation**: Thuật toán nhanh cho real-time feedback
  
- **Features**:
  - Heterogeneity Correction (Batho, Modified Batho, Equivalent TAR)
  - Multi-energy Calculation
  - Tissue Assignment
  - Dose-to-medium vs Dose-to-water
  - Statistical Uncertainty Estimation

### 5. Optimization (Tối Ưu Hóa)
- **Objective Functions**:
  - Target Coverage (Mean, Min, Max Dose)
  - Normal Tissue Complication Probability (NTCP)
  - Tumor Control Probability (TCP)
  - Equivalent Uniform Dose (EUD)
  - Dose-Volume Constraints
  
- **Optimization Engines**:
  - Simulated Annealing
  - Gradient-based Methods
  - Genetic Algorithms
  - Multi-objective Optimization
  
- **IMRT/VMAT Specific**:
  - Fluence Optimization
  - Leaf Sequencing
  - Arc Geometry Optimization
  - Dose Rate Modulation

### 6. Visualization (Trực Quan Hóa)
- **2D/3D Viewers**:
  - Multi-planar Reconstruction (Axial, Coronal, Sagittal, Oblique)
  - Maximum Intensity Projection (MIP)
  - Volume Rendering
  - Interactive Window/Level adjustment
  
- **Dose Display**:
  - Colorwash Overlay
  - Isodose Lines với customizable levels
  - Dose Profiles
  - Gamma Analysis Visualization
  
- **Analysis Tools**:
  - Dose-Volume Histogram (DVH)
  - Plan Comparison (Side-by-side, Difference maps)
  - Statistical Analysis
  - Beam's Eye View (BEV)
  - Room's Eye View

### 7. Quality Assurance
- **Plan Check**:
  - Automated Plan Review
  - Physics Check List
  - Machine Parameter Validation
  - Dose Constraint Verification
  
- **Statistical Analysis**:
  - Plan Quality Metrics
  - Population-based Analysis
  - Trend Analysis
  - Outcome Correlation

## Dữ Liệu Commissioning

### Truebeam Beam Data
Dự án bao gồm dữ liệu commissioning đầy đủ cho máy gia tốc Varian Truebeam:

#### Photon Beams:
- **4MV**: Open fields, Wedged fields (15°, 30°, 45°, 60°)
- **6MV**: Open fields, Wedged fields (15°, 30°, 45°, 60°)
- **8MV**: Open fields, Wedged fields (15°, 30°, 45°, 60°)
- **10MV**: Open fields, Wedged fields (15°, 30°, 45°, 60°)
- **15MV**: Open fields, Wedged fields (15°, 30°, 45°, 60°)
- **6FFF**: Flattening Filter Free
- **10FFF**: Flattening Filter Free

#### Electron Beams:
- **Energies**: 6, 9, 12, 15, 16, 18, 20, 22 MeV
- **Cutouts**: Various applicator sizes
- **Algorithms**: eMC và GGPB data

#### Data Types:
- **Percentage Depth Dose (PDD)**: Cho các field sizes khác nhau
- **Beam Profiles (PRF)**: In-plane và cross-plane
- **Diagonal Profiles**: Đánh giá penumbra
- **Output Factors**: Normalized output tương ứng với field size
- **Wedge Factors**: Transmission factors cho các wedge angles
- **Scatter Factors**: Phantom scatter và collimator scatter

## Kiến Trúc Hệ Thống

### Design Patterns
- **Model-View-Controller (MVC)**: Tách biệt logic nghiệp vụ và giao diện
- **Observer Pattern**: Cập nhật real-time giữa các components
- **Factory Pattern**: Tạo objects tùy theo algorithm được chọn
- **Strategy Pattern**: Linh hoạt chọn algorithm tính liều
- **Command Pattern**: Undo/Redo functionality

### Threading & Performance
- **Multi-threading**: Parallel processing cho dose calculation
- **GPU Acceleration**: Hỗ trợ CUDA/OpenCL cho algorithms phức tạp
- **Memory Management**: Efficient handling của large datasets
- **Caching System**: Cache kết quả tính toán để tăng tốc

### Database Architecture
- **SQLite**: Local database cho development
- **PostgreSQL**: Production database với advanced features
- **ORM**: SQLAlchemy cho database abstraction
- **Migration**: Alembic cho database schema changes

## Công Nghệ Sử Dụng

### Core Libraries
- **Python 3.8+**: Ngôn ngữ chính
- **NumPy**: Tính toán numerical
- **SciPy**: Scientific computing
- **Matplotlib**: Plotting và visualization
- **OpenCV**: Image processing
- **SimpleITK**: Medical image processing
- **PyQt5/PySide2**: GUI framework

### Medical Imaging
- **pydicom**: DICOM file handling
- **nibabel**: NIfTI và các format khác
- **itk**: Insight Toolkit integration
- **vtk**: Visualization Toolkit

### Scientific Computing
- **scikit-image**: Image processing algorithms
- **scikit-learn**: Machine learning tools
- **pandas**: Data analysis
- **h5py**: HDF5 file format

### Optimization
- **scipy.optimize**: Built-in optimizers
- **CVXPY**: Convex optimization
- **DEAP**: Evolutionary algorithms
- **Numba**: JIT compilation for speed

## Installation & Setup

### System Requirements
- **OS**: Windows 10+, Linux Ubuntu 18.04+, macOS 10.14+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10GB+ free space
- **GPU**: Optional - CUDA-capable GPU cho acceleration

### Installation Steps
```bash
# Clone repository
git clone https://github.com/yourusername/tps.git
cd tps

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Initialize database
python scripts/init_database.py

# Import beam data
python scripts/import_beam_data.py

# Run application
python main.py
```

## Development Workflow

### Code Style
- **PEP 8**: Python code style guide
- **Type Hints**: Sử dụng typing annotations
- **Docstrings**: Google style docstrings
- **Black**: Code formatter
- **Pylint**: Code analysis

### Testing
- **pytest**: Test framework
- **Coverage**: Test coverage analysis
- **Mock**: Mock objects cho unit testing
- **Continuous Integration**: GitHub Actions

### Version Control
- **Git Flow**: Branching model
- **Semantic Versioning**: Version numbering
- **Conventional Commits**: Commit message format

## API Documentation

### Core APIs
```python
# Patient Management
from src.core.patient_manager import PatientManager
pm = PatientManager()
patient = pm.load_patient(patient_id)

# Image Processing
from src.core.image_processor import ImageProcessor
ip = ImageProcessor()
ct_images = ip.load_dicom_series(dicom_path)

# Dose Calculation
from src.dose_calculation.algorithms.pencil_beam import PencilBeamCalculator
calc = PencilBeamCalculator()
dose = calc.calculate_dose(plan, ct_images)

# Optimization
from src.optimization.imrt_optimizer import IMRTOptimizer
opt = IMRTOptimizer()
optimized_plan = opt.optimize(initial_plan, objectives, constraints)
```

## Configuration

### Machine Configuration
```json
{
  "machine_name": "Truebeam_STx",
  "energies": ["6MV", "10MV", "15MV", "6FFF", "10FFF"],
  "max_field_size": [40.0, 40.0],
  "sad": 100.0,
  "mlc": {
    "type": "Millennium120",
    "leaf_width": [0.5, 1.0],
    "max_speed": 2.5
  }
}
```

### Algorithm Configuration
```json
{
  "default_algorithm": "AAA",
  "algorithms": {
    "PBC": {
      "grid_size": 2.5,
      "smoothing": true
    },
    "AAA": {
      "grid_size": 1.0,
      "heterogeneity_correction": true
    }
  }
}
```

## Roadmap

### Phase 1: Core Infrastructure (Completed)
- ✅ Project structure setup
- ✅ DICOM I/O functionality
- ✅ Basic GUI framework
- ✅ Database schema

### Phase 2: Basic Planning (In Progress)
- 🔄 Patient management system
- 🔄 Image viewer implementation
- 🔄 Basic contouring tools
- ⏳ Simple dose calculation

### Phase 3: Advanced Features
- ⏳ IMRT/VMAT optimization
- ⏳ Advanced visualization
- ⏳ Quality assurance tools
- ⏳ Reporting system

### Phase 4: Clinical Integration
- ⏳ ARIA integration
- ⏳ Clinical workflows
- ⏳ User training materials
- ⏳ Validation testing

### Future Enhancements
- 🔮 AI-powered auto-contouring
- 🔮 Adaptive radiotherapy
- 🔮 Real-time plan monitoring
- 🔮 Cloud-based processing

## Contributing

### Development Guidelines
1. Fork repository và tạo feature branch
2. Implement changes với appropriate tests
3. Ensure code quality (lint, format, test)
4. Submit pull request với detailed description
5. Code review và integration

### Bug Reports
- Sử dụng GitHub Issues
- Provide detailed reproduction steps
- Include system information
- Attach relevant log files

## License

Dự án này được phân phối dưới giấy phép MIT License. Xem file `LICENSE` để biết thêm chi tiết.

## Support & Contact

- **Documentation**: [Wiki Page](https://github.com/yourusername/tps/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/tps/issues)
- **Email**: support@tps-project.com
- **Community**: [Discord Server](https://discord.gg/tps-community)

---

**Lưu ý**: Đây là phần mềm nghiên cứu và phát triển. Không được sử dụng cho mục đích lâm sàng mà không qua validation và certification process phù hợp.
