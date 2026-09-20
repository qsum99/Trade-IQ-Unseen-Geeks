"""Pytest collection support for Samarth's unittest-style suite.

His tests use `from helpers import ...` (stdlib unittest runner convention).
This conftest puts this directory on sys.path so the SAME files also run
under pytest from the backend root. No test files modified.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
