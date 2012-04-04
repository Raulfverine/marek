#!/usr/bin/python
from setuptools import setup, find_packages


def get_deb_meta():
    with open("debian/changelog") as chlog:
        data = chlog.read()
    return dict(
        name=data[0],
        version=data[1][1:-1]
    )


setup(
    packages = find_packages(),
    **get_deb_meta()
)
