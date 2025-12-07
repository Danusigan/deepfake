"""
File handling module - WITH ANIMATED GIF IN TARGET WINDOW
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
from PIL import Image, ImageOps
import cv2
from .utils import create_animated_gif_preview, stop_all_animations

# UI references
_root = None
_status_label = None
_target_label = None
_source_label = None
_output_label = None
_qr_code_label = None
_capture_btn = None

# NEW: Store the actual Supabase URLs
_last_supabase_image_url = None
_last_supabase_qr_url = None

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_OUTPUT = None

# Categories
TARGETS_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'targets'))
CATEGORIES = {
    "Male": os.path.join(TARGETS_ROOT_DIR, 'Male'),
    "Female": os.path.join(TARGETS_ROOT_DIR, 'Female'), 
    "Children": os.path.join(TARGETS_ROOT_DIR, 'Children'),
    "Trending": os.path.join(TARGETS_ROOT_DIR, 'Trending gif')
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
    
    print("[DEBUG] File handler refs initialized")


def update_status(text: str):
    """Update status label"""
    if _status_label:
        _status_label.configure(text=text)
    if _root:
        _root.update_idletasks()


def is_gif(path: str) -> bool:
    """Check if file is a GIF"""
    return path and path.lower().endswith('.gif')


def render_image_preview_contain(path: str, size: tuple) -> ctk.CTkImage:
    """Render image using CONTAIN mode"""
    try:
        img = ImageOps.contain(Image.open(path), size, Image.LANCZOS)
        return ctk.CTkImage(img, size=img.size)
    except Exception as e:
        print(f"[ERROR] Image render: {e}")
        blank = Image.new('RGB', size, '#2b2b2b')
        return ctk.CTkImage(blank, size=size)


def render_video_preview_contain(path: str, size: tuple) -> ctk.CTkImage:
    """Render video using CONTAIN mode"""
    try:
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = ImageOps.contain(img, size, Image.LANCZOS)
            return ctk.CTkImage(img, size=img.size)
    except Exception as e:
        print(f"[ERROR] Video render: {e}")
    
    blank = Image.new('RGB', size, '#2b2b2b')
    return ctk.CTkImage(blank, size=size)


def select_source_path(path: Optional[str] = None):
    """Select source image"""
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
            
            preview_img = render_image_preview_contain(path, (280, 180))
            _source_label.configure(image=preview_img, text="")
            _source_label.image = preview_img
            
            _capture_btn.configure(text='📸 Capture Face')
            update_status(f"Source: {os.path.basename(path)}")
            print(f"[DEBUG] Source set: {path}")
        except Exception as e:
            print(f"[ERROR] Source: {e}")
            update_status(f"Error: {e}")
    elif not path and camera_state['is_open']:
        start_camera_feed()


def select_target_path(path: Optional[str] = None):
    """Select target media"""
    from .dialogs import TargetBrowserDialog
    from .preview import close_preview
    from roop.face_reference import clear_face_reference
    
    close_preview()
    clear_face_reference()
    
    print("[DEBUG] select_target_path")
    
    if roop.globals.PIPELINE_ENABLED:
        update_status("⚠️ Pipeline mode active")
        return
    
    if not path:
        if not os.path.isdir(TARGETS_ROOT_DIR):
            update_status(f"Error: Targets dir not found")
            return
        TargetBrowserDialog(_root, CATEGORIES, handle_target_selection, pipeline_mode=False)
    else:
        handle_target_selection(path)


def handle_target_selection(path):
    """Handle target selection - WITH ANIMATED GIF IN TARGET WINDOW"""
    print(f"[DEBUG] handle_target_selection: {path}")
    
    if path:
        path = path.strip('{}').strip()
    
    # CRITICAL: Stop animations and reset output
    stop_all_animations()
    
    if _output_label:
        _output_label.configure(image="", text="Process to view result")
        _output_label.image = None
    
    if _qr_code_label:
        _qr_code_label.configure(image="", text="QR Code")
        _qr_code_label.image = None
    
    # Force UI update
    if _root:
        _root.update()
    
    try:
        if path and is_image(path):
            roop.globals.target_path = path
            preview_img = render_image_preview_contain(path, (280, 180))
            _target_label.configure(image=preview_img, text="")
            _target_label.image = preview_img
            update_status(f"Target: {os.path.basename(path)}")
            print("[DEBUG] Target image set")
            
        elif path and is_gif(path):
            roop.globals.target_path = path
            update_status(f"Loading GIF: {os.path.basename(path)}")
            print(f"[DEBUG] Starting GIF animation for target: {path}")
            # CRITICAL: Start animated GIF in target window
            if _root and _target_label:
                _root.after(150, lambda: show_animated_target_preview(path))
            else:
                print("[DEBUG] ERROR: _root or _target_label is None!")
            
        elif path and is_video(path):
            roop.globals.target_path = path
            preview_img = render_video_preview_contain(path, (280, 180))
            _target_label.configure(image=preview_img, text="")
            _target_label.image = preview_img
            update_status(f"Target Video: {os.path.basename(path)}")
            print("[DEBUG] Target video set")
    
    except Exception as e:
        print(f"[ERROR] Target selection: {e}")
        import traceback
        traceback.print_exc()


def show_animated_target_preview(gif_path):
    """Show ANIMATED GIF in target preview window"""
    print(f"[DEBUG] show_animated_target_preview called: {gif_path}")
    print(f"[DEBUG] _target_label: {_target_label}")
    print(f"[DEBUG] _root: {_root}")
    
    try:
        if _target_label and _root:
            print("[DEBUG] Creating animated GIF preview for target...")
            success = create_animated_gif_preview(gif_path, (280, 180), _target_label, _root)
            if success:
                update_status(f"✅ GIF playing: {os.path.basename(gif_path)}")
                print("[DEBUG] ✅ Target GIF animation started successfully!")
            else:
                print("[DEBUG] ❌ GIF animation failed, using static fallback")
                preview_img = render_image_preview_contain(gif_path, (280, 180))
                _target_label.configure(image=preview_img, text="")
                _target_label.image = preview_img
                update_status(f"GIF: {os.path.basename(gif_path)}")
        else:
            print(f"[DEBUG] ❌ Cannot animate: _target_label={_target_label}, _root={_root}")
    except Exception as e:
        print(f"[ERROR] Target GIF animation: {e}")
        import traceback
        traceback.print_exc()


def select_output_path(start_callback: Callable[[], None]):
    """Select output and start processing"""
    global RECENT_DIRECTORY_OUTPUT
    
    print("[DEBUG] select_output_path")
    
    if roop.globals.PIPELINE_ENABLED:
        update_status("⚠️ Pipeline mode")
        return
    
    if not roop.globals.target_path:
        update_status("Select target first!")
        return
    
    if not roop.globals.source_path:
        update_status("Select source first!")
        return
    
    target_path = roop.globals.target_path
    
    if is_gif(target_path):
        ext = '.gif'
        file_type = "GIF"
    elif is_video(target_path):
        ext = '.mp4'
        file_type = "Video"
    elif has_image_extension(target_path):
        ext = '.png'
        file_type = "Image"
    else:
        update_status("❌ Unknown file type!")
        return
    
    timestamp = int(time.time())
    output_filename = f"output_{timestamp}{ext}"
    roop.globals.output_path = os.path.join(roop.globals.FIXED_OUTPUT_DIR, output_filename)
    
    print(f"[DEBUG] Output: {roop.globals.output_path}")
    update_status(f"⚡ Processing {file_type}...")
    
    if _root:
        _root.update_idletasks()
    
    # Start processing
    print("[DEBUG] Starting callback")
    start_callback()
    
    # Schedule output display
    delay = 3000 if is_gif(target_path) else 2000
    print(f"[DEBUG] Scheduling output check in {delay}ms")
    if _root:
        _root.after(delay, lambda: check_and_display_output(roop.globals.output_path))


def store_supabase_urls(image_url: str, qr_url: str):
    """Store Supabase URLs for QR generation"""
    global _last_supabase_image_url, _last_supabase_qr_url
    _last_supabase_image_url = image_url
    _last_supabase_qr_url = qr_url
    print(f"[DEBUG] Stored Supabase URLs: image={image_url}, qr={qr_url}")


def check_and_display_output(path):
    """Display output - WITH ANIMATED GIF AND FULLSCREEN"""
    print(f"[DEBUG] check_and_display_output: {path}")
    
    try:
        if not os.path.exists(path):
            print(f"[DEBUG] File not found, retrying...")
            if _root:
                _root.after(1000, lambda: check_and_display_output(path))
            return
        
        file_size = os.path.getsize(path)
        print(f"[DEBUG] File exists: {file_size} bytes")
        
        if file_size == 0:
            print("[DEBUG] File empty, retrying...")
            if _root:
                _root.after(500, lambda: check_and_display_output(path))
            return
        
        update_status(f"📦 Loading: {os.path.basename(path)}")
        
        if _root:
            _root.update_idletasks()
        
        # Stop previous animations
        stop_all_animations()
        
        if is_gif(path):
            print("[DEBUG] Displaying output GIF")
            update_status("✅ GIF complete!")
            if _root:
                _root.after(200, lambda: show_animated_output_preview(path))
                # Show fullscreen GIF
                _root.after(400, lambda: _show_fullscreen_output(path))
        elif is_video(path):
            print("[DEBUG] Displaying video")
            prev = render_video_preview_contain(path, (350, 200))
            if _output_label and prev:
                _output_label.configure(image=prev, text="")
                _output_label.image = prev
            update_status("✅ Video complete!")
            # Show fullscreen video
            if _root:
                _root.after(500, lambda: _show_fullscreen_output(path))
        elif is_image(path):
            print("[DEBUG] Displaying image")
            prev = render_image_preview_contain(path, (350, 200))
            if _output_label and prev:
                _output_label.configure(image=prev, text="")
                _output_label.image = prev
            update_status("✅ Image complete!")
            # Show fullscreen image
            if _root:
                _root.after(500, lambda: _show_fullscreen_output(path))
        
        # Force update
        if _root:
            _root.update()
        
        # QR code - NOW USES REAL SUPABASE URL
        if _root:
            _root.after(400, lambda: generate_qr_for_output())
        
        print("[DEBUG] Output displayed")
        
    except Exception as e:
        print(f"[ERROR] Display: {e}")
        import traceback
        traceback.print_exc()


def _show_fullscreen_output(path):
    """Display output in fullscreen"""
    print(f"[DEBUG] _show_fullscreen_output: {path}")
    try:
        from .fullscreen_display import show_output_fullscreen
        show_output_fullscreen(path, _root)
    except Exception as e:
        print(f"[ERROR] Fullscreen display: {e}")
        import traceback
        traceback.print_exc()


def show_animated_output_preview(gif_path):
    """Show ANIMATED GIF in output preview"""
    print(f"[DEBUG] show_animated_output_preview: {gif_path}")
    try:
        if _output_label and _root:
            success = create_animated_gif_preview(gif_path, (350, 200), _output_label, _root)
            if success:
                update_status(f"✅ GIF playing!")
                print("[DEBUG] Output GIF animation started")
            else:
                print("[DEBUG] Animation failed")
                prev = render_image_preview_contain(gif_path, (350, 200))
                _output_label.configure(image=prev, text="")
                _output_label.image = prev
    except Exception as e:
        print(f"[ERROR] Output GIF: {e}")
        import traceback
        traceback.print_exc()


def generate_qr_for_output():
    """Generate QR code using REAL Supabase URL - BIGGER SIZE"""
    global _last_supabase_image_url
    
    print(f"[DEBUG] Generating QR with URL: {_last_supabase_image_url}")
    
    try:
        if _qr_code_label and _last_supabase_image_url:
            # Use the REAL Supabase URL that was uploaded
            # BIGGER QR CODE: 300x300 instead of 180x180
            qr_img = generate_qr_code(_last_supabase_image_url, (300, 300))
            _qr_code_label.configure(image=qr_img, text="")
            _qr_code_label.image = qr_img
            print("[DEBUG] QR generated with real Supabase URL (300x300)")
        else:
            print(f"[DEBUG] Cannot generate QR: label={_qr_code_label}, url={_last_supabase_image_url}")
    except Exception as e:
        print(f"[ERROR] QR: {e}")


def get_categories():
    return CATEGORIES

def get_targets_root_dir():
    return TARGETS_ROOT_DIR