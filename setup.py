"""Setuptools Module."""
from setuptools import setup, find_packages

setup(
    name="githubutils",
    version="0.1",
    packages=find_packages(),
    install_requires=['requests'],
    # metadata for upload to PyPI
    author="Alexander Richards",
    author_email="a.richards@imperial.ac.uk",
    description="Utilities for working with github",
    license="MIT",
    url="https://github.com/alexanderrichards/GithubUtils"
)
