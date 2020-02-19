"""
Your friendly synthetic data generator
"""

from .primitive_generators import *
from .derived_generators import Apply
from .custom_generator import CustomGenerator

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
