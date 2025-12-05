"""
File handling module - Updated for correct paths and fixed exports
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
from roop.utilities import is_image, is_video
from roop.qr_generator import generate_qr_code
from .utils import render_image_preview, render_video_preview

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

# Categories for target browser - UPDATED PATH
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


def select_source_path(path: Optional[str] = None):
    """Select source image file"""
    from .camera import get_camera_state, start_camera_feed
    from .preview import close_preview
    
    global RECENT_DIRECTORY_SOURCE
    
    # Pause camera feed
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
            _capture_btn.configure(text='📸 Capture Face', command=lambda: __import__('ui.camera', fromlist=['do_capture']).do_capture())
            update_status(f"Source: {os.path.basename(path)}")
        except Exception as e:
            update_status(f"Error: {e}")
    elif not path and camera_state['is_open']:
        # Resume camera
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
    """Handle target file selection"""
    if path:
        path = path.strip('{}').strip()
    
    if path and is_image(path):
        roop.globals.target_path = path
        _target_label.configure(image=render_image_preview(path, (280, 180)), text="")
        update_status(f"Target: {os.path.basename(path)}")
    elif path and is_video(path):
        roop.globals.target_path = path
        _target_label.configure(image=render_video_preview(path, (280, 180)), text="")
        update_status(f"Target: {os.path.basename(path)}")


def select_output_path(start_callback: Callable[[], None]):
    """Select output file path and start processing"""
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
    
    ext = '.png' if is_image(roop.globals.target_path) else '.mp4' if is_video(roop.globals.target_path) else None
    if not ext:
        return
    
    timestamp = int(time.time())
    output_filename = f"output_{timestamp}{ext}"
    roop.globals.output_path = os.path.join(roop.globals.FIXED_OUTPUT_DIR, output_filename)
    
    update_status(f"Output will be saved to: {output_filename}")
    _root.update()
    
    start_callback()
    _root.after(1000, lambda: check_and_display_output(roop.globals.output_path))


def check_and_display_output(path):
    """Check if output exists and display it"""
    try:
        if os.path.exists(path):
            if is_image(path):
                prev = render_image_preview(path, (350, 200))
            else:
                prev = render_video_preview(path, (350, 200))
            _output_label.configure(image=prev, text="")
            generate_qr_for_output(path)
    except Exception as e:
        print(f"Error displaying output: {e}")


def generate_qr_for_output(path: str):
    """Generate QR code for output file"""
    try:
        if _qr_code_label:
            qr_img = generate_qr_code(f"https://envlcgzlopkallmmtcaq.supabase.co/storage/v1/object/public/images/generated/{os.path.basename(path)}", (180, 180))
            _qr_code_label.configure(image=qr_img, text="")
            
            if _output_label:
                if is_image(path):
                    prev = render_image_preview(path, (350, 200))
                elif is_video(path):
                    prev = render_video_preview(path, (350, 200))
                else:
                    return
                _output_label.configure(image=prev, text="")
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