"""
Pipeline mode module with timer functionality
Contains pipeline processing functions with 60s countdown
"""

import os
import roop.globals

# UI references
_root = None
_capture_btn = None
_timer_frame = None
_timer_label = None
_next_cycle_btn = None
_countdown_after_id = None
_remaining_seconds = 60


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
        stop_countdown()
        hide_timer_ui()
        
        # Don't auto-disable camera
        camera_var = get_camera_switch_var()
        if camera_var and camera_var.get():
            from .file_handlers import update_status as status_update
            status_update("Camera still active - toggle manually if needed")


def handle_pipeline_target_selection(path):
    """Handle target selection for pipeline"""
    from .file_handlers import update_status
    from .utils import render_image_preview, render_video_preview
    from .main_window import get_target_label
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
    
    # AUTO-ENABLE CAMERA FOR PIPELINE
    from .camera import enable_camera_for_pipeline
    _root.after(800, enable_camera_for_pipeline)


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
        _root.after(1500, start_cycle_timer)
    except Exception as e:
        update_status(f"Pipeline error: {str(e)}")
        prompt_pipeline_recapture()


def start_cycle_timer():
    """Start 60-second countdown timer for next cycle"""
    from .file_handlers import update_status
    global _remaining_seconds
    
    if not roop.globals.PIPELINE_ENABLED:
        return
    
    _remaining_seconds = 60
    show_timer_ui()
    update_status("⏱️ Next cycle starts in 60 seconds...")
    countdown_tick()


def countdown_tick():
    """Update countdown timer"""
    global _remaining_seconds, _countdown_after_id
    
    if not roop.globals.PIPELINE_ENABLED:
        stop_countdown()
        return
    
    if _timer_label:
        mins = _remaining_seconds // 60
        secs = _remaining_seconds % 60
        _timer_label.configure(text=f"⏱️ Next Cycle: {mins:02d}:{secs:02d}")
    
    if _remaining_seconds > 0:
        _remaining_seconds -= 1
        _countdown_after_id = _root.after(1000, countdown_tick)
    else:
        # Timer finished - start next cycle
        start_next_cycle()


def stop_countdown():
    """Stop the countdown timer"""
    global _countdown_after_id
    if _countdown_after_id is not None:
        try:
            _root.after_cancel(_countdown_after_id)
        except:
            pass
        _countdown_after_id = None


def start_next_cycle():
    """Start the next pipeline cycle"""
    from .file_handlers import update_status, get_categories
    from .dialogs import TargetBrowserDialog
    from .main_window import get_root, get_source_label
    
    stop_countdown()
    hide_timer_ui()
    
    if not roop.globals.PIPELINE_ENABLED:
        return
    
    update_status("🔄 Starting next cycle - Select new target...")
    
    # Reset source
    roop.globals.source_path = None
    roop.globals.PIPELINE_AUTO_TARGET = None
    
    # Reset source label to default
    source_label = get_source_label()
    if source_label:
        source_label.configure(image=None, text="Drag & Drop Image\nor Click to Select\n\nOr toggle camera ON")
    
    # Reset capture button
    if _capture_btn:
        _capture_btn.configure(text='📸 Capture Face', state='disabled', fg_color="#00bcd4")
    
    # Open target browser for new target selection
    # This will eventually call handle_pipeline_target_selection -> enable_camera_for_pipeline
    root = get_root()
    categories = get_categories()
    TargetBrowserDialog(root, categories, handle_pipeline_target_selection, pipeline_mode=True)


def show_timer_ui():
    """Show timer UI elements"""
    global _timer_frame, _timer_label, _next_cycle_btn
    
    if _timer_frame is not None:
        return  # Already exists
    
    import customtkinter as ctk
    from .main_window import get_root
    
    root = get_root()
    
    # Create timer frame with overlay effect
    _timer_frame = ctk.CTkFrame(root, fg_color="#1a1f2e", corner_radius=15, 
                                border_width=2, border_color="#E91E63")
    _timer_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    # Timer label
    _timer_label = ctk.CTkLabel(
        _timer_frame,
        text="⏱️ Time Remaining: 01:00",
        font=("Segoe UI", 28, "bold"),
        text_color="#00E5FF"
    )
    _timer_label.pack(padx=50, pady=(25, 15))
    
    # Next cycle button
    _next_cycle_btn = ctk.CTkButton(
        _timer_frame,
        text="⚡ Go with another person now",
        font=("Segoe UI", 15, "bold"),
        fg_color="#E91E63",
        hover_color="#C2185B",
        height=45,
        width=280,
        corner_radius=10,
        command=start_next_cycle
    )
    _next_cycle_btn.pack(padx=50, pady=(10, 25))


def hide_timer_ui():
    """Hide and destroy timer UI elements"""
    global _timer_frame, _timer_label, _next_cycle_btn
    
    if _timer_frame is not None:
        _timer_frame.destroy()
        _timer_frame = None
        _timer_label = None
        _next_cycle_btn = None


def prompt_pipeline_recapture():
    """Prompt for next capture in pipeline"""
    from .file_handlers import update_status
    from .camera import get_camera_state, do_capture
    
    if not roop.globals.PIPELINE_ENABLED:
        return
    
    roop.globals.source_path = None
    _capture_btn.configure(text='📸 Capture Next Face', command=do_capture, state='normal')
    
    update_status("🔄 Ready for next capture - Pipeline active")


def get_timer_state():
    """Get current timer state"""
    return {
        'is_running': _countdown_after_id is not None,
        'remaining_seconds': _remaining_seconds
    }