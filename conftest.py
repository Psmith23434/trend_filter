"""pytest configuration — adds project root to sys.path so imports work."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
