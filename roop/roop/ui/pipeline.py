"""
Pipeline mode module
Contains pipeline processing functions
"""

import os
import roop.globals

# UI references
_root = None
_capture_btn = None


def init_pipeline_references(root, capture_btn):
    """Initialize references to UI components"""
    global _root, _capture_btn
    _root = root
    _capture_btn = capture_btn


def handle_pipeline_toggle():
    """Handle pipeline mode toggle"""
    from .file_handlers import update_status, get_targets_root_dir, get_categories
    from .dialogs import TargetBrowserDialog
    from .main_window import get_pipeline_switch_var, get_camera_switch_var, get_root
    
    pipeline_var = get_pipeline_switch_var()
    roop.globals.PIPELINE_ENABLED = pipeline_var.get()
    
    if roop.globals.PIPELINE_ENABLED:
        update_status("⚡ Pipeline Mode ACTIVATED")
        
        # Create output directory
        if not os.path.exists(roop.globals.FIXED_OUTPUT_DIR):
            try:
                os.makedirs(roop.globals.FIXED_OUTPUT_DIR, exist_ok=True)
                update_status(f"✓ Output directory created")
            except Exception as e:
                update_status(f"Error: Cannot create output directory")
                pipeline_var.set(False)
                roop.globals.PIPELINE_ENABLED = False
                return
        
        # Check targets directory
        targets_root = get_targets_root_dir()
        if not os.path.isdir(targets_root):
            update_status("Error: Targets directory not found!")
            pipeline_var.set(False)
            roop.globals.PIPELINE_ENABLED = False
            return
        
        # Open target browser
        update_status("Select target media for pipeline...")
        root = get_root()
        categories = get_categories()
        TargetBrowserDialog(root, categories, handle_pipeline_target_selection, pipeline_mode=True)
    else:
        update_status("Pipeline Mode DISABLED - Normal mode active")
        roop.globals.PIPELINE_AUTO_TARGET = None
        
        camera_var = get_camera_switch_var()
        if camera_var and camera_var.get():
            camera_var.set(False)
            from .camera import handle_camera_toggle
            handle_camera_toggle()


def handle_pipeline_target_selection(path):
    """Handle target selection for pipeline"""
    from .file_handlers import update_status
    from .utils import render_image_preview, render_video_preview
    from .main_window import get_target_label, get_camera_switch_var, get_root
    from roop.utilities import is_image, is_video
    
    roop.globals.PIPELINE_AUTO_TARGET = path
    roop.globals.target_path = path
    
    target_label = get_target_label()
    if target_label:
        if is_image(path):
            target_label.configure(image=render_image_preview(path, (280, 180)), text="")
        elif is_video(path):
            target_label.configure(image=render_video_preview(path, (280, 180)), text="")
    
    update_status(f"✓ Pipeline target set: {os.path.basename(path)}")
    
    # Enable camera
    camera_var = get_camera_switch_var()
    if camera_var and not camera_var.get():
        camera_var.set(True)
        root = get_root()
        root.after(500, lambda: __import__('ui.camera', fromlist=['handle_camera_toggle']).handle_camera_toggle())
    
    update_status("📷 Camera enabled - Capture face to start pipeline")


def pipeline_process():
    """Process in pipeline mode"""
    from .file_handlers import update_status
    
    if not roop.globals.PIPELINE_ENABLED:
        return
    
    if not roop.globals.source_path:
        update_status("Error: No source face captured!")
        prompt_pipeline_recapture()
        return
    
    if not roop.globals.PIPELINE_AUTO_TARGET:
        update_status("Error: No target selected for pipeline!")
        prompt_pipeline_recapture()
        return
    
    roop.globals.target_path = roop.globals.PIPELINE_AUTO_TARGET
    update_status("⚡ Processing in pipeline mode...")
    _root.update()
    
    try:
        from roop.core import start as core_start
        core_start()
        update_status(f"✓ Pipeline complete! Saved to Outputs folder")
        _root.after(1500, prompt_pipeline_recapture)
    except Exception as e:
        update_status(f"Pipeline error: {str(e)}")
        prompt_pipeline_recapture()


def prompt_pipeline_recapture():
    """Prompt for next capture in pipeline"""
    from .file_handlers import update_status
    from .camera import get_camera_state, start_camera_feed, do_capture
    
    if not roop.globals.PIPELINE_ENABLED:
        return
    
    roop.globals.source_path = None
    _capture_btn.configure(text='📸 Capture Next Face', command=do_capture, state='normal')
    
    camera_state = get_camera_state()
    if camera_state['is_open']:
        start_camera_feed()
        update_status("🔄 Ready for next capture - Pipeline active")
    else:
        update_status("⚠️ Camera disconnected - toggle camera to continue pipeline")