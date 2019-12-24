from setuptools import setup, find_packages

print( find_packages())
setup(
    name="pdcam",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'pdcam-cli = pdcam.scripts.main:main',
        ],
    },
    dependency_links=['https://github.com/sushil-bharati/pyzbar/tarball/master#egg=pyzbar-1.0']
    install_requires=[
        'click',
        'numpy',
    ],
)