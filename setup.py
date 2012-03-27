#!/usr/bin/python
from setuptools import setup, find_packages

setup (
    name = "marek",
    version = open("debian/changelog").read().split()[1][1:-1],
    packages = find_packages()
)
