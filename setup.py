#!/usr/bin/env python3
"""
Setuptools configuration for the Speechmatics Flow client
"""

import logging
import os

from setuptools import setup, find_packages


def read(fname):
    """
    Load content of the file with path relative to where setup.py is.

    Args:
        fname (str): file name (or path relative to the project root)

    Returns:
        str: file content
    """
    fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    with open(fpath, encoding="utf-8") as path:
        return path.read()


def read_list(fname):
    """
    Load the content of the file and split it into a list of lines.

    Args:
        fname (str): file name (or path relative to the project root)

    Returns:
        List[str]: file content (one string per line) with end-of-lines
                   characters stripped off and empty lines filtered out
    """
    content = read(fname)
    retval = list(filter(None, content.split("\n")))

    return retval


def get_version(fname):
    """
    Retrieve the version from the VERSION file.

    Args:
        fname (str): file containing only the version

    Returns:
        str: version with whitespace characters stripped off
    """
    return read(fname).strip()


logging.basicConfig(level=logging.INFO)
setup(
    name="speechmatics-flow",
    version=os.getenv("VERSION", get_version("VERSION")),
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/speechmatics/speechmatics-flow/",
    license="MIT",
    author="Speechmatics",
    author_email="support@speechmatics.com",
    description="Python library and CLI for Speechmatics Flow API",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    install_requires=read_list("requirements.txt"),
    tests_require=read_list("requirements-dev.txt"),
    entry_points={
        "console_scripts": ["speechmatics-flow = speechmatics_flow.cli:main"]
    },
    project_urls={
        "Documentation": "https://speechmatics.github.io/speechmatics-flow/",
        "Source Code": "https://github.com/speechmatics/speechmatics-flow/",
    },
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    include_package_data=True,
    python_requires=">=3.7",
)
