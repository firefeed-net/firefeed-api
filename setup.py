"""
Setup script for FireFeed API

This module provides setuptools configuration for the FireFeed API package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')

# Read development requirements
dev_requirements = []
dev_requirements_file = this_directory / "requirements-dev.txt"
if dev_requirements_file.exists():
    dev_requirements = dev_requirements_file.read_text().strip().split('\n')

setup(
    name="firefeed-api",
    version="1.0.0",
    author="FireFeed Team",
    author_email="mail@firefeed.net",
    description="API service for FireFeed RSS reader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/firefeed-net/firefeed-api",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "firefeed-api=firefeed_api.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "firefeed_api": ["py.typed"],
    },
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/firefeed/firefeed-api/issues",
        "Source": "https://github.com/firefeed/firefeed-api",
        "Documentation": "https://firefeed.github.io/firefeed-api/",
    },
)