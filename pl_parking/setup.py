#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration for Wheel Build."""
import sys
from pathlib import Path

import setuptools
from pl_parking import __version__ as VERSION

ROOT = Path(__file__).resolve().parent
if ROOT not in sys.path:
    sys.path.append(str(ROOT))

__author__ = "<CHANGE ME>"
__copyright__ = "2020-2023, Continental BA ADAS"
__status__ = "Production"

with open(ROOT / "requirements.txt", "r") as f:
    install_requires = [line.rstrip() for line in f]

packages = setuptools.find_packages(include=["pl_parking*"])

setuptools.setup(
    name="adas-pl-parking",
    version=VERSION,
    author="A AM ENP SIMU KPI",
    author_email="info@noreply.de",
    description="PL Parking Repository",
    long_description="-",
    long_description_content_type="text/plain",
    url="https://github-am.geo.conti.de/ADAS/pl_parking",
    packages=packages,
    include_package_data=True,
    install_requires=install_requires,
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Testing",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [],
    },
)
