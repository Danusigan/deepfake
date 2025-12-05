"""
Roop package initialization
"""

__version__ = '1.0.0'

# Only expose what's necessary for the core functionality
from .core import run
# new export for Supabase upload utility
from .supabase_utils import upload_image_and_generate_qr

__all__ = ['run', 'upload_image_and_generate_qr']