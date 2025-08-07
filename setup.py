"""
Setup script cho TPS - Treatment Planning System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="tps",
    version="0.1.0",
    description="Hệ thống lập kế hoạch xạ trị (Treatment Planning System)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TPS Development Team", 
    author_email="tps-dev@example.com",
    url="https://github.com/yourusername/tps",
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Entry points
    entry_points={
        "console_scripts": [
            "tps=main:main",
        ],
    },
    
    # Package data
    package_data={
        "": ["*.txt", "*.md", "*.json", "*.yaml", "*.yml"],
    },
    include_package_data=True,
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
    ],
    
    # Keywords
    keywords="radiotherapy treatment planning medical imaging dicom",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/yourusername/tps/issues",
        "Source": "https://github.com/yourusername/tps",
        "Documentation": "https://github.com/yourusername/tps/wiki",
    },
    
    # Extras
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0", 
            "black>=21.9.0",
            "pylint>=2.11.0",
            "sphinx>=4.0.0",
        ],
        "gpu": [
            "cupy-cuda11x>=9.6.0",
            "pycuda>=2021.1",
        ],
    },
)
