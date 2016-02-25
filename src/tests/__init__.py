import os
import sys

_instdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_instdir = os.path.join(_instdir,"lib")
sys.path.append(_instdir)
