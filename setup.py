"""Setuptools configuration for Nldi Xstool."""
from os import path

from setuptools import find_packages
from setuptools import setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

here = path.abspath(path.dirname(__file__))
with open(path.join(here, "requirements.txt")) as requirements_file:
    # Parse requirements.txt, ignoring any commented-out lines.
    requirements = [
        line
        for line in requirements_file.read().splitlines()
        if not line.startswith("#")
    ]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="Richard McDonald",
    author_email="rmcd@usgs.gov",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    description="Generate cross-sections using 3DEP supplied topography.",
    entry_points={
        "console_scripts": [
            "nldi-xstool=nldi_xstool.__main__:main",
        ],
    },
    install_requires=requirements,
    license="MIT",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="nldi_xstool,nldi-xstool",
    name="nldi_xstool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/rmcd-mscb/nldi-xstool",
    version="0.0.1-dev0",
    zip_safe=False,
)
