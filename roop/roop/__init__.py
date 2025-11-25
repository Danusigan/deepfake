"""
Roop package initialization
"""

__version__ = '1.0.0'

# Only expose what's necessary for the core functionality
from .core import run

__all__ = ['run']