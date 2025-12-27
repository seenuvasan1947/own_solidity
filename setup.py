from setuptools import setup, find_packages
import os

# Read the contents of README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name="ptsscan",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive Solidity source code security scanner - PTS Edition",
    long_description=read_file("README.md") if os.path.exists("README.md") else "A comprehensive Solidity source code security scanner - PTS Edition",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ptsscan",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "antlr4-python3-runtime>=4.9.0",
        "openpyxl>=3.0.0",
        "colorama>=0.4.0",
        "tqdm>=4.60.0",
    ],
    entry_points={
        "console_scripts": [
            "ptsscan=ptsscan.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ptsscan": ["*.g4", "*.tokens", "*.interp"],
    },
)
