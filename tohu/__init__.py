"""
Your friendly synthetic data generator
"""

from .primitive_generators import *
from .derived_generators import Apply
from .custom_generator import CustomGenerator
from .custom_generator_NEW import CustomGeneratorNEW
from .custom_generator_NEW_3 import CustomGeneratorNEW3
from .foreach import foreach
from .foreach_NEW_3 import foreach_NEW3
from .logging import logger as tohu_logger

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
