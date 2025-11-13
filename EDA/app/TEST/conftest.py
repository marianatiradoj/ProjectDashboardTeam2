# app/TEST/conftest.py
import sys, os

APP = os.path.dirname(os.path.dirname(__file__))  # .../app
if APP not in sys.path:
    sys.path.insert(0, APP)
