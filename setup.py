from setuptools import setup, find_packages

setup(
    name="schoolphotoID",
    version="1.0.0",
    description="School Photo Face Recognition and Identification Desktop Application",
    author="SchoolFacerecognition",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.5.0",
        "face-recognition>=1.3.0",
        "dlib>=19.24.0",
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "schoolphotoID=schoolphotoID.main:main",
        ],
    },
)