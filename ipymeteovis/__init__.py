import os

from .temp import *
from .task import *
from .view import *

if __import__("ipymeteovis"):
    # Make selection directory if not exist
    if not os.path.exists(TEMP_SET_PATH):
        os.mkdir(TEMP_SET_PATH)