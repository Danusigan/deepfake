"""
File handling module - Fixed for Video/GIF support with animated previews
"""

from typing import Optional, Callable
import os
import time
import customtkinter as ctk
try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
import roop.globals
from roop.utilities import is_image, is_video, has_image_extension
from roop.qr_generator import generate_qr_code
from .utils import render_image_preview, render_video_preview, create_animated_gif_preview

# UI references
_root = None
_status_label = None
_target_label = None
_source_label = None
_output_label = None
_qr_code_label = None
_capture_btn = None

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_OUTPUT = None

# Categories for target browser
TARGETS_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'targets'))
CATEGORIES = {
    "Male": os.path.join(TARGETS_ROOT_DIR, 'Male'),
    "Female": os.path.join(TARGETS_ROOT_DIR, 'Female'), 
    "Children": os.path.join(TARGETS_ROOT_DIR, 'Children')
}


def init_file_handler_references(root, status_label, target_label, source_label, 
                                 output_label, qr_code_label, capture_btn):
    """Initialize references to UI components"""
    global _root, _status_label, _target_label, _source_label, _output_label, _qr_code_label, _capture_btn
    _root = root
    _status_label = status_label
    _target_label = target_label
    _source_label = source_label
    _output_label = output_label
    _qr_code_label = qr_code_label
    _capture_btn = capture_btn


def update_status(text: str):
    """Update status label"""
    if _status_label:
        _status_label.configure(text=text)
    if _root:
        _root.update_idletasks()


def is_gif(path: str) -> bool:
    """Check if file is a GIF"""
    return path.lower().endswith('.gif')


def select_source_path(path: Optional[str] = None):
    """Select source image file"""
    from .camera import get_camera_state, start_camera_feed
    from .preview import close_preview
    
    global RECENT_DIRECTORY_SOURCE
    
    camera_state = get_camera_state()
    close_preview()
    
    if not path:
        path = ctk.filedialog.askopenfilename(
            title='Select source image',
            initialdir=RECENT_DIRECTORY_SOURCE,
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")]
        )
    
    if path:
        path = path.strip('{}').strip()
    
    if path and is_image(path):
        try:
            roop.globals.source_path = path
            RECENT_DIRECTORY_SOURCE = os.path.dirname(path)
            _source_label.configure(image=render_image_preview(path, (280, 180)), text="")
            _capture_btn.configure(text='📸 Capture Face', command=lambda: __import__('roop.ui.camera', fromlist=['do_capture']).do_capture())
            update_status(f"Source: {os.path.basename(path)}")
        except Exception as e:
            update_status(f"Error: {e}")
    elif not path and camera_state['is_open']:
        start_camera_feed()


def select_target_path(path: Optional[str] = None):
    """Select target media file"""
    from .dialogs import TargetBrowserDialog
    from .preview import close_preview
    from roop.face_reference import clear_face_reference
    
    close_preview()
    clear_face_reference()
    
    if roop.globals.PIPELINE_ENABLED:
        update_status("⚠️ Pipeline mode active - target already set")
        return
    
    if not path:
        if not os.path.isdir(TARGETS_ROOT_DIR):
            update_status(f"Error: Root target directory '{TARGETS_ROOT_DIR}' not found.")
            return
        TargetBrowserDialog(_root, CATEGORIES, handle_target_selection, pipeline_mode=False)
    else:
        handle_target_selection(path)


def handle_target_selection(path):
    """Handle target file selection with animated preview support"""
    if path:
        path = path.strip('{}').strip()
    
    if path and is_image(path):
        roop.globals.target_path = path
        _target_label.configure(image=render_image_preview(path, (280, 180)), text="")
        update_status(f"Target: {os.path.basename(path)}")
    elif path and is_gif(path):
        roop.globals.target_path = path
        # Show animated GIF preview
        update_status(f"Loading GIF: {os.path.basename(path)}")
        _root.after(100, lambda: show_animated_target_preview(path))
    elif path and is_video(path):
        roop.globals.target_path = path
        # Show video thumbnail
        _target_label.configure(image=render_video_preview(path, (280, 180)), text="")
        update_status(f"Target Video: {os.path.basename(path)}")
        # Add video icon overlay
        _root.after(100, lambda: add_video_indicator(_target_label))


def show_animated_target_preview(gif_path):
    """Show animated GIF in target preview"""
    try:
        animated_preview = create_animated_gif_preview(gif_path, (280, 180), _target_label, _root)
        if animated_preview:
            update_status(f"✅ GIF loaded: {os.path.basename(gif_path)}")
        else:
            # Fallback to static preview
            _target_label.configure(image=render_image_preview(gif_path, (280, 180)), text="")
            update_status(f"GIF: {os.path.basename(gif_path)} (static preview)")
    except Exception as e:
        update_status(f"Error loading GIF: {e}")


def add_video_indicator(label):
    """Add visual indicator that this is a video"""
    # This is handled in the UI - just update status
    update_status(f"📹 Video loaded - will process all frames")


def select_output_path(start_callback: Callable[[], None]):
    """Select output file path and start processing - FIXED for video/GIF detection"""
    global RECENT_DIRECTORY_OUTPUT
    
    if roop.globals.PIPELINE_ENABLED:
        update_status("⚠️ Pipeline mode active - outputs auto-saved")
        return
    
    if not roop.globals.target_path:
        update_status("Select target first!")
        return
    
    if not roop.globals.source_path:
        update_status("Select or capture source face first!")
        return
    
    # FIXED: Proper extension detection
    target_path = roop.globals.target_path
    
    if is_gif(target_path):
        ext = '.gif'  # GIF output
        file_type = "GIF"
    elif is_video(target_path):
        ext = '.mp4'  # Video output
        file_type = "Video"
    elif has_image_extension(target_path):
        ext = '.png'  # Image output
        file_type = "Image"
    else:
        update_status("❌ Unknown file type!")
        return
    
    timestamp = int(time.time())
    output_filename = f"output_{timestamp}{ext}"
    roop.globals.output_path = os.path.join(roop.globals.FIXED_OUTPUT_DIR, output_filename)
    
    update_status(f"⚡ Processing {file_type}... Output: {output_filename}")
    _root.update()
    
    start_callback()
    _root.after(1000, lambda: check_and_display_output(roop.globals.output_path))


def check_and_display_output(path):
    """Check if output exists and display it with animation support"""
    try:
        if os.path.exists(path):
            if is_gif(path):
                # Show animated output GIF
                update_status("✅ GIF processing complete! Displaying...")
                _root.after(100, lambda: show_animated_output_preview(path))
            elif is_video(path):
                # Show video thumbnail
                prev = render_video_preview(path, (350, 200))
                _output_label.configure(image=prev, text="")
                update_status("✅ Video processing complete!")
                add_video_player_hint()
            elif is_image(path):
                # Show image
                prev = render_image_preview(path, (350, 200))
                _output_label.configure(image=prev, text="")
                update_status("✅ Image processing complete!")
            
            # Generate QR code
            generate_qr_for_output(path)
    except Exception as e:
        print(f"Error displaying output: {e}")
        update_status(f"Output saved but preview error: {e}")


def show_animated_output_preview(gif_path):
    """Show animated GIF in output preview"""
    try:
        animated_preview = create_animated_gif_preview(gif_path, (350, 200), _output_label, _root)
        if animated_preview:
            update_status(f"✅ GIF complete! Playing in preview...")
        else:
            _output_label.configure(image=render_image_preview(gif_path, (350, 200)), text="")
    except Exception as e:
        update_status(f"GIF saved but preview error: {e}")


def add_video_player_hint():
    """Add hint for video playback"""
    update_status("📹 Video saved! Click output to play in media player")


def generate_qr_for_output(path: str):
    """Generate QR code for output file"""
    try:
        if _qr_code_label:
            qr_img = generate_qr_code(f"https://share.roop/{os.path.basename(path)}", (180, 180))
            _qr_code_label.configure(image=qr_img, text="")
            
            # Don't re-display output, it's already shown above
    except Exception as e:
        print(f"Error generating QR code: {e}")
        if _qr_code_label:
            _qr_code_label.configure(text="QR Failed")


def get_categories():
    """Get target categories"""
    return CATEGORIES


def get_targets_root_dir():
    """Get targets root directory"""
    return TARGETS_ROOT_DIR