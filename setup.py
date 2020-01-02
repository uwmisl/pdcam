from setuptools import setup, find_packages

print( find_packages())
setup(
    name="pdcam",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'pdcam = pdcam.scripts.main:main',
        ],
    },
    install_requires=[
        'apriltag',
        'click',
        'flask',
        'flask-cors',
        'matplotlib',
        'numpy',
    ],
    extras_require={
        'testing': [
            'pytest',
            'pytest_benchmark',
        ],
    },
)