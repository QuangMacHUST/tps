"""
Module xử lý hình ảnh y tế

Chức năng:
- Load và xử lý images từ các định dạng khác nhau
- Chuyển đổi giữa các format (DICOM, NIfTI, Analyze, etc.)
- Image preprocessing và enhancement
- Geometric transformations
- Windowing và display operations
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import nibabel as nib
import SimpleITK as sitk

# Cấu hình logging
logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats"""
    DICOM = "dicom"
    NIFTI = "nifti"  
    ANALYZE = "analyze"
    NRRD = "nrrd"
    MHD = "mhd"
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"


@dataclass
class ImageProperties:
    """Thông tin thuộc tính của ảnh"""
    shape: Tuple[int, ...] 
    spacing: Tuple[float, ...]
    origin: Tuple[float, ...]
    direction: Tuple[float, ...]
    dtype: str
    pixel_type: str = "unknown"
    components: int = 1
    
    # Medical imaging specific
    modality: Optional[str] = None
    study_date: Optional[str] = None
    series_description: Optional[str] = None
    
    # Display properties
    window_center: Optional[float] = None
    window_width: Optional[float] = None
    
    
@dataclass
class WindowLevel:
    """Window/Level settings cho display"""
    center: float
    width: float
    name: str = ""
    
    @property
    def min_value(self) -> float:
        return self.center - self.width / 2
    
    @property 
    def max_value(self) -> float:
        return self.center + self.width / 2


class ImageProcessor:
    """
    Xử lý hình ảnh y tế
    
    Hỗ trợ:
    - Multi-format loading (DICOM, NIfTI, NRRD, etc.)
    - Image preprocessing
    - Geometric transformations  
    - Display optimizations
    - Format conversions
    """
    
    # Predefined window/level presets
    WINDOW_PRESETS = {
        'CT': {
            'bone': WindowLevel(400, 1500, "Bone"),
            'soft_tissue': WindowLevel(50, 350, "Soft Tissue"),
            'lung': WindowLevel(-600, 1600, "Lung"),
            'brain': WindowLevel(40, 80, "Brain"),
            'abdomen': WindowLevel(60, 400, "Abdomen"),
            'mediastinum': WindowLevel(50, 350, "Mediastinum")
        },
        'MRI': {
            't1': WindowLevel(500, 1000, "T1"),
            't2': WindowLevel(1000, 2000, "T2"),
            'flair': WindowLevel(800, 1600, "FLAIR"),
            'dwi': WindowLevel(800, 1600, "DWI")
        }
    }
    
    def __init__(self):
        """Khởi tạo ImageProcessor"""
        logger.info("ImageProcessor được khởi tạo")
    
    def load_image_sitk(self, file_path: str) -> Optional[sitk.Image]:
        """
        Load image sử dụng SimpleITK
        
        Args:
            file_path: Đường dẫn file ảnh
            
        Returns:
            sitk.Image hoặc None nếu lỗi
        """
        try:
            image = sitk.ReadImage(file_path)
            logger.info(f"Loaded image: {file_path}, Size: {image.GetSize()}")
            return image
        except Exception as e:
            logger.error(f"Lỗi load image {file_path}: {e}")
            return None
    
    def load_dicom_series(self, dicom_dir: str) -> Optional[sitk.Image]:
        """
        Load DICOM series từ thư mục
        
        Args:
            dicom_dir: Đường dẫn thư mục DICOM
            
        Returns:
            sitk.Image hoặc None nếu lỗi
        """
        try:
            reader = sitk.ImageSeriesReader()
            dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir)
            
            if not dicom_names:
                logger.error(f"Không tìm thấy DICOM series trong {dicom_dir}")
                return None
            
            reader.SetFileNames(dicom_names)
            image = reader.Execute()
            
            logger.info(f"Loaded DICOM series: {len(dicom_names)} files, Size: {image.GetSize()}")
            return image
            
        except Exception as e:
            logger.error(f"Lỗi load DICOM series {dicom_dir}: {e}")
            return None
    
    def load_nifti(self, file_path: str) -> Optional[np.ndarray]:
        """
        Load NIfTI file
        
        Args:
            file_path: Đường dẫn NIfTI file
            
        Returns:
            np.ndarray hoặc None nếu lỗi
        """
        try:
            nii = nib.load(file_path)
            image_data = nii.get_fdata()
            logger.info(f"Loaded NIfTI: {file_path}, Shape: {image_data.shape}")
            return image_data
        except Exception as e:
            logger.error(f"Lỗi load NIfTI {file_path}: {e}")
            return None
    
    def get_image_properties(self, image: sitk.Image) -> ImageProperties:
        """
        Lấy thông tin thuộc tính của ảnh
        
        Args:
            image: SimpleITK image
            
        Returns:
            ImageProperties
        """
        try:
            props = ImageProperties(
                shape=image.GetSize(),
                spacing=image.GetSpacing(),
                origin=image.GetOrigin(), 
                direction=image.GetDirection(),
                dtype=str(image.GetPixelID()),
                pixel_type=image.GetPixelIDTypeAsString(),
                components=image.GetNumberOfComponentsPerPixel()
            )
            
            # Try to get DICOM metadata
            try:
                for key in image.GetMetaDataKeys():
                    if "0008|0060" in key:  # Modality
                        props.modality = image.GetMetaData(key)
                    elif "0008|103e" in key:  # Series Description
                        props.series_description = image.GetMetaData(key)
                    elif "0008|0020" in key:  # Study Date
                        props.study_date = image.GetMetaData(key)
                    elif "0028|1050" in key:  # Window Center
                        props.window_center = float(image.GetMetaData(key))
                    elif "0028|1051" in key:  # Window Width
                        props.window_width = float(image.GetMetaData(key))
            except:
                pass
            
            return props
            
        except Exception as e:
            logger.error(f"Lỗi lấy image properties: {e}")
            # Return basic properties
            return ImageProperties(
                shape=image.GetSize() if image else (0,),
                spacing=(1.0, 1.0, 1.0),
                origin=(0.0, 0.0, 0.0),
                direction=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0),
                dtype="unknown"
            )
    
    def convert_to_numpy(self, image: sitk.Image) -> np.ndarray:
        """
        Convert SimpleITK image sang NumPy array
        
        Args:
            image: SimpleITK image
            
        Returns:
            np.ndarray
        """
        try:
            array = sitk.GetArrayFromImage(image)
            # SimpleITK uses (z,y,x) order, transpose to (x,y,z)
            if array.ndim == 3:
                array = np.transpose(array, (2, 1, 0))
            elif array.ndim == 2:
                array = np.transpose(array, (1, 0))
            
            logger.debug(f"Converted to numpy array shape: {array.shape}")
            return array
        except Exception as e:
            logger.error(f"Lỗi convert to numpy: {e}")
            return np.array([])
    
    def convert_from_numpy(self, array: np.ndarray, 
                          spacing: Tuple[float, ...] = None,
                          origin: Tuple[float, ...] = None) -> sitk.Image:
        """
        Convert NumPy array sang SimpleITK image
        
        Args:
            array: NumPy array
            spacing: Pixel spacing
            origin: Image origin
            
        Returns:
            sitk.Image
        """
        try:
            # Transpose back to SimpleITK order
            if array.ndim == 3:
                array = np.transpose(array, (2, 1, 0))
            elif array.ndim == 2:
                array = np.transpose(array, (1, 0))
            
            image = sitk.GetImageFromArray(array)
            
            if spacing:
                image.SetSpacing(spacing)
            if origin:
                image.SetOrigin(origin)
            
            logger.debug(f"Converted from numpy array shape: {array.shape}")
            return image
        except Exception as e:
            logger.error(f"Lỗi convert from numpy: {e}")
            return sitk.Image()
    
    def apply_window_level(self, array: np.ndarray, window: WindowLevel) -> np.ndarray:
        """
        Áp dụng window/level cho display
        
        Args:
            array: Image array
            window: WindowLevel settings
            
        Returns:
            np.ndarray: Windowed image (0-255)
        """
        try:
            # Clip values to window range
            windowed = np.clip(array, window.min_value, window.max_value)
            
            # Normalize to 0-255
            if window.width > 0:
                windowed = (windowed - window.min_value) / window.width * 255
            else:
                windowed = np.zeros_like(windowed)
            
            return windowed.astype(np.uint8)
            
        except Exception as e:
            logger.error(f"Lỗi apply window/level: {e}")
            return array.astype(np.uint8)
    
    def auto_window_level(self, array: np.ndarray, percentile: float = 2.0) -> WindowLevel:
        """
        Tự động tính window/level từ histogram
        
        Args:
            array: Image array
            percentile: Percentile để loại bỏ outliers
            
        Returns:
            WindowLevel
        """
        try:
            # Remove outliers
            lower = np.percentile(array, percentile)
            upper = np.percentile(array, 100 - percentile)
            
            center = (lower + upper) / 2
            width = upper - lower
            
            return WindowLevel(center=center, width=width, name="Auto")
            
        except Exception as e:
            logger.error(f"Lỗi auto window/level: {e}")
            # Return default window
            return WindowLevel(center=np.mean(array), width=np.std(array) * 4)
    
    def resize_image(self, image: sitk.Image, new_size: Tuple[int, ...],
                    interpolator: int = sitk.sitkLinear) -> sitk.Image:
        """
        Resize image
        
        Args:
            image: Input image
            new_size: Target size
            interpolator: Interpolation method
            
        Returns:
            sitk.Image: Resized image
        """
        try:
            # Calculate new spacing to maintain physical dimensions
            original_size = image.GetSize()
            original_spacing = image.GetSpacing()
            
            new_spacing = tuple(
                orig_spacing * (orig_size / new_size)
                for orig_spacing, orig_size, new_size in 
                zip(original_spacing, original_size, new_size)
            )
            
            # Create resampler
            resampler = sitk.ResampleImageFilter()
            resampler.SetOutputSpacing(new_spacing)
            resampler.SetSize(new_size)
            resampler.SetOutputDirection(image.GetDirection())
            resampler.SetOutputOrigin(image.GetOrigin())
            resampler.SetTransform(sitk.Transform())
            resampler.SetDefaultPixelValue(0)
            resampler.SetInterpolator(interpolator)
            
            resized = resampler.Execute(image)
            logger.info(f"Resized image from {original_size} to {new_size}")
            return resized
            
        except Exception as e:
            logger.error(f"Lỗi resize image: {e}")
            return image
    
    def rotate_image(self, image: sitk.Image, angle_degrees: float, 
                    center: Tuple[float, ...] = None) -> sitk.Image:
        """
        Xoay ảnh theo góc
        
        Args:
            image: Input image
            angle_degrees: Góc xoay (độ)
            center: Tâm xoay (nếu None sẽ dùng center of image)
            
        Returns:
            sitk.Image: Rotated image
        """
        try:
            dimension = image.GetDimension()
            
            if dimension == 2:
                # 2D rotation
                if center is None:
                    center = [sz * spc / 2.0 for sz, spc in zip(image.GetSize(), image.GetSpacing())]
                
                transform = sitk.Euler2DTransform()
                transform.SetCenter(center)
                transform.SetAngle(np.radians(angle_degrees))
                
            elif dimension == 3:
                # 3D rotation around Z axis
                if center is None:
                    center = [sz * spc / 2.0 for sz, spc in zip(image.GetSize(), image.GetSpacing())]
                
                transform = sitk.Euler3DTransform()
                transform.SetCenter(center)
                transform.SetRotation(0, 0, np.radians(angle_degrees))
            else:
                logger.error(f"Unsupported dimension for rotation: {dimension}")
                return image
            
            # Resample with transform
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(image)
            resampler.SetTransform(transform)
            resampler.SetInterpolator(sitk.sitkLinear)
            resampler.SetDefaultPixelValue(0)
            
            rotated = resampler.Execute(image)
            logger.info(f"Rotated image by {angle_degrees} degrees")
            return rotated
            
        except Exception as e:
            logger.error(f"Lỗi rotate image: {e}")
            return image
    
    def flip_image(self, image: sitk.Image, axes: List[bool]) -> sitk.Image:
        """
        Lật ảnh theo các trục
        
        Args:
            image: Input image
            axes: List bool cho từng trục (True = flip)
            
        Returns:
            sitk.Image: Flipped image
        """
        try:
            flip_filter = sitk.FlipImageFilter()
            flip_filter.SetFlipAxes(axes)
            flipped = flip_filter.Execute(image)
            
            logger.info(f"Flipped image along axes: {axes}")
            return flipped
            
        except Exception as e:
            logger.error(f"Lỗi flip image: {e}")
            return image
    
    def enhance_contrast(self, array: np.ndarray, method: str = "clahe") -> np.ndarray:
        """
        Tăng cường độ tương phản
        
        Args:
            array: Image array (8-bit)
            method: Enhancement method ("clahe", "histogram_eq", "gamma")
            
        Returns:
            np.ndarray: Enhanced image
        """
        try:
            if method == "clahe":
                # CLAHE (Contrast Limited Adaptive Histogram Equalization)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                if array.ndim == 2:
                    enhanced = clahe.apply(array)
                else:
                    enhanced = np.zeros_like(array)
                    for i in range(array.shape[0]):
                        enhanced[i] = clahe.apply(array[i])
                        
            elif method == "histogram_eq":
                # Global histogram equalization
                if array.ndim == 2:
                    enhanced = cv2.equalizeHist(array)
                else:
                    enhanced = np.zeros_like(array)
                    for i in range(array.shape[0]):
                        enhanced[i] = cv2.equalizeHist(array[i])
                        
            elif method == "gamma":
                # Gamma correction
                gamma = 1.5
                enhanced = np.power(array / 255.0, 1.0 / gamma) * 255
                enhanced = enhanced.astype(np.uint8)
            else:
                logger.warning(f"Unknown enhancement method: {method}")
                enhanced = array
            
            logger.info(f"Enhanced contrast using method: {method}")
            return enhanced
            
        except Exception as e:
            logger.error(f"Lỗi enhance contrast: {e}")
            return array
    
    def denoise_image(self, array: np.ndarray, method: str = "bilateral") -> np.ndarray:
        """
        Khử nhiễu ảnh
        
        Args:
            array: Image array
            method: Denoising method ("bilateral", "gaussian", "median")
            
        Returns:
            np.ndarray: Denoised image
        """
        try:
            if method == "bilateral":
                # Bilateral filter - preserves edges
                if array.ndim == 2:
                    denoised = cv2.bilateralFilter(array, 9, 75, 75)
                else:
                    denoised = np.zeros_like(array)
                    for i in range(array.shape[0]):
                        denoised[i] = cv2.bilateralFilter(array[i], 9, 75, 75)
                        
            elif method == "gaussian":
                # Gaussian blur
                if array.ndim == 2:
                    denoised = cv2.GaussianBlur(array, (5, 5), 1.0)
                else:
                    denoised = np.zeros_like(array)
                    for i in range(array.shape[0]):
                        denoised[i] = cv2.GaussianBlur(array[i], (5, 5), 1.0)
                        
            elif method == "median":
                # Median filter
                if array.ndim == 2:
                    denoised = cv2.medianBlur(array, 5)
                else:
                    denoised = np.zeros_like(array)
                    for i in range(array.shape[0]):
                        denoised[i] = cv2.medianBlur(array[i], 5)
            else:
                logger.warning(f"Unknown denoising method: {method}")
                denoised = array
            
            logger.info(f"Denoised image using method: {method}")
            return denoised
            
        except Exception as e:
            logger.error(f"Lỗi denoise image: {e}")
            return array
    
    def save_image(self, image: sitk.Image, file_path: str, 
                  format_type: ImageFormat = None) -> bool:
        """
        Lưu ảnh ra file
        
        Args:
            image: SimpleITK image
            file_path: Đường dẫn output file
            format_type: Format output (auto-detect nếu None)
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Auto-detect format từ extension nếu không specify
            if format_type is None:
                ext = Path(file_path).suffix.lower()
                format_map = {
                    '.nii': ImageFormat.NIFTI,
                    '.nii.gz': ImageFormat.NIFTI,
                    '.nrrd': ImageFormat.NRRD,
                    '.mhd': ImageFormat.MHD,
                    '.png': ImageFormat.PNG,
                    '.jpg': ImageFormat.JPEG,
                    '.jpeg': ImageFormat.JPEG,
                    '.tiff': ImageFormat.TIFF,
                    '.tif': ImageFormat.TIFF
                }
                format_type = format_map.get(ext, ImageFormat.NIFTI)
            
            # Tạo thư mục nếu cần
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            sitk.WriteImage(image, file_path)
            
            logger.info(f"Saved image: {file_path} (format: {format_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi save image {file_path}: {e}")
            return False
    
    def convert_format(self, input_path: str, output_path: str, 
                      target_format: ImageFormat) -> bool:
        """
        Convert ảnh giữa các format
        
        Args:
            input_path: Đường dẫn file input
            output_path: Đường dẫn file output  
            target_format: Format đích
            
        Returns:
            bool: True nếu thành công
        """
        try:
            # Load image
            image = self.load_image_sitk(input_path)
            if image is None:
                return False
            
            # Save in target format
            return self.save_image(image, output_path, target_format)
            
        except Exception as e:
            logger.error(f"Lỗi convert format {input_path} -> {output_path}: {e}")
            return False
    
    def create_thumbnail(self, array: np.ndarray, size: Tuple[int, int] = (128, 128),
                        slice_index: int = None) -> np.ndarray:
        """
        Tạo thumbnail từ image array
        
        Args:
            array: Image array
            size: Thumbnail size
            slice_index: Index của slice (cho 3D image, None = middle slice)
            
        Returns:
            np.ndarray: Thumbnail image
        """
        try:
            # Get 2D slice from 3D array
            if array.ndim == 3:
                if slice_index is None:
                    slice_index = array.shape[0] // 2  # Middle slice
                slice_2d = array[slice_index]
            else:
                slice_2d = array
            
            # Auto window/level
            window = self.auto_window_level(slice_2d)
            windowed = self.apply_window_level(slice_2d, window)
            
            # Resize
            thumbnail = cv2.resize(windowed, size, interpolation=cv2.INTER_AREA)
            
            logger.debug(f"Created thumbnail {size} from array {array.shape}")
            return thumbnail
            
        except Exception as e:
            logger.error(f"Lỗi create thumbnail: {e}")
            # Return empty thumbnail
            return np.zeros(size, dtype=np.uint8)
    
    def get_image_statistics(self, array: np.ndarray) -> Dict[str, float]:
        """
        Tính toán thống kê cơ bản của ảnh
        
        Args:
            array: Image array
            
        Returns:
            Dict: Thống kê values
        """
        try:
            # Exclude zero values for medical images
            non_zero = array[array > 0] if np.any(array > 0) else array.flatten()
            
            stats = {
                'mean': float(np.mean(non_zero)),
                'std': float(np.std(non_zero)),
                'min': float(np.min(non_zero)),
                'max': float(np.max(non_zero)),
                'median': float(np.median(non_zero)),
                'q25': float(np.percentile(non_zero, 25)),
                'q75': float(np.percentile(non_zero, 75)),
                'voxel_count': int(non_zero.size),
                'total_voxels': int(array.size)
            }
            
            logger.debug(f"Image statistics: mean={stats['mean']:.2f}, std={stats['std']:.2f}")
            return stats
            
        except Exception as e:
            logger.error(f"Lỗi get image statistics: {e}")
            return {}
