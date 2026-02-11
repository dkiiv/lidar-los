#!/usr/bin/env python3

from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "los",
        ["los.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++"
    ),
]

setup(
    name="los",
    ext_modules=ext_modules,
)