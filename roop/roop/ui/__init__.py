"""
UI Module - Entry point for the Roop UI
Exposes the main functions needed by core.py
"""

from .main_window import init, get_root, get_target_label, get_pipeline_switch_var, get_camera_switch_var
from .file_handlers import update_status, generate_qr_for_output, get_categories, get_targets_root_dir, check_and_display_output
from .camera import destroy_camera, handle_camera_toggle, get_camera_state
from .pipeline import handle_pipeline_toggle, pipeline_process, init_pipeline_references
from .preview import toggle_preview, close_preview

# Export main interface functions
__all__ = [
    'init', 'get_root', 'get_target_label', 'get_pipeline_switch_var', 'get_camera_switch_var',
    'update_status', 'generate_qr_for_output', 'get_categories', 'get_targets_root_dir', 'check_and_display_output',
    'destroy_camera', 'handle_camera_toggle', 'get_camera_state',
    'handle_pipeline_toggle', 'pipeline_process', 'init_pipeline_references',
    'toggle_preview', 'close_preview'
]