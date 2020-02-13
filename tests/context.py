import os
import sys

# This inserts the parent directory into the path so that when
# we import the package it will pick it up from here and doesn't
# require it to be installed. This guarantees the tests are always
# run against the up-to-date version in this directory and not
# against some potentially outdated version that happens to be
# installed in some environment.
#
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tohu
