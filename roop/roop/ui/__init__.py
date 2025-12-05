"""
UI Module - Entry point for the Roop UI
Exposes the main functions needed by core.py
"""

from .main_window import init, get_root, get_target_label, get_pipeline_switch_var, get_camera_switch_var
from .file_handlers import update_status, generate_qr_for_output, get_categories, get_targets_root_dir, check_and_display_output
from .camera import destroy_camera, handle_camera_toggle, get_camera_state
from .pipeline import handle_pipeline_toggle, pipeline_process, init_pipeline_references

# Try to import preview functions, but don't fail if they don't exist
try:
    from .preview import toggle_preview, close_preview
    HAS_PREVIEW = True
except ImportError:
    HAS_PREVIEW = False
    def toggle_preview():
        pass
    def close_preview():
        pass

# Export main interface functions
__all__ = [
    'init', 'get_root', 'get_target_label', 'get_pipeline_switch_var', 'get_camera_switch_var',
    'update_status', 'generate_qr_for_output', 'get_categories', 'get_targets_root_dir', 'check_and_display_output',
    'destroy_camera', 'handle_camera_toggle', 'get_camera_state',
    'handle_pipeline_toggle', 'pipeline_process', 'init_pipeline_references',
    'toggle_preview', 'close_preview'
]