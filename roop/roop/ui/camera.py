"""
Camera handling module - Fix for 2nd Cycle Feed Issue
"""

import cv2
import time
import os
import tempfile
from PIL import Image, ImageOps
import customtkinter as ctk
import roop.globals

# Camera state
CAM_OBJECT = None
CAM_IS_RUNNING = False
CAM_AFTER_ID = None
CAM_FRAME_DATA = None
CAM_CURRENT_IMAGE = None  # Keep single current reference

# UI references
_root = None
_source_label = None
_capture_btn = None
_camera_switch_var = None

def init_camera_references(root, source_label, capture_btn, camera_switch_var):
    global _root, _source_label, _capture_btn, _camera_switch_var
    _root = root
    _source_label = source_label
    _capture_btn = capture_btn
    _camera_switch_var = camera_switch_var

def stop_camera_feed():
    """Stop camera feed without releasing camera"""
    global CAM_IS_RUNNING, CAM_AFTER_ID
    CAM_IS_RUNNING = False
    if CAM_AFTER_ID is not None:
        try:
            _root.after_cancel(CAM_AFTER_ID)
        except:
            pass
        CAM_AFTER_ID = None

def release_camera():
    """Fully release camera hardware"""
    global CAM_OBJECT, CAM_FRAME_DATA, CAM_CURRENT_IMAGE
    
    stop_camera_feed()
    
    # Keep reference until fully released
    CAM_CURRENT_IMAGE = None
    CAM_FRAME_DATA = None
    
    if CAM_OBJECT is not None:
        try:
            CAM_OBJECT.release()
        except:
            pass
        finally:
            CAM_OBJECT = None
    
    # Extra cleanup
    time.sleep(0.3)
    try:
        cv2.destroyAllWindows()
    except:
        pass

def destroy_camera():
    """Complete camera cleanup"""
    release_camera()

def open_camera():
    """Open camera with proper initialization"""
    global CAM_OBJECT
    
    # Ensure previous instance is closed
    if CAM_OBJECT is not None:
        release_camera()
        time.sleep(1.2)
    
    # Try DirectShow (Windows - more stable)
    CAM_OBJECT = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    time.sleep(0.7)
    
    if not CAM_OBJECT or not CAM_OBJECT.isOpened():
        CAM_OBJECT = cv2.VideoCapture(0)
        time.sleep(0.7)
    
    if CAM_OBJECT and CAM_OBJECT.isOpened():
        # Configure camera
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        CAM_OBJECT.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Warm up - discard first frames
        for _ in range(10):
            ret, frame = CAM_OBJECT.read()
            if ret and frame is not None:
                time.sleep(0.05)
        
        # Final test
        ret, frame = CAM_OBJECT.read()
        if ret and frame is not None:
            return True
    
    release_camera()
    return False

def handle_camera_toggle():
    """Handle camera on/off toggle"""
    from .file_handlers import update_status
    global CAM_IS_RUNNING
    
    if _camera_switch_var.get():
        update_status("Opening camera...")
        _root.update()
        
        if open_camera():
            CAM_IS_RUNNING = True
            _capture_btn.configure(state='normal', text='📸 Capture Face', fg_color="#00bcd4")
            start_camera_feed()
            update_status("Camera ON - Live feed active")
        else:
            _camera_switch_var.set(False)
            _capture_btn.configure(state='disabled')
            update_status("❌ Cannot open camera! Close other apps")
    else:
        release_camera()
        _capture_btn.configure(state='disabled', text='📸 Capture Face')
        if not roop.globals.source_path:
            _source_label.configure(image='', text="Drag & Drop Image\nor Click to Select\n\nOr toggle camera ON")
        update_status("Camera OFF")

def start_camera_feed():
    """Start displaying camera feed"""
    global CAM_IS_RUNNING
    # Prevent double starting
    if CAM_IS_RUNNING and CAM_AFTER_ID is not None:
        return
        
    CAM_IS_RUNNING = True
    # Initial delay before first tick
    _root.after(150, camera_feed_tick)

def camera_feed_tick():
    """Update camera feed display - main loop"""
    global CAM_AFTER_ID, CAM_FRAME_DATA, CAM_CURRENT_IMAGE
    
    if not CAM_IS_RUNNING:
        return
    
    # Check camera is valid
    if not CAM_OBJECT or not CAM_OBJECT.isOpened():
        _camera_switch_var.set(False)
        from .file_handlers import update_status
        update_status("Camera disconnected")
        return
    
    try:
        # Read frame
        ret, frame = CAM_OBJECT.read()
        
        if ret and frame is not None and frame.size > 0:
            # Store for capture
            CAM_FRAME_DATA = frame.copy()
            
            # Process for display
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = ImageOps.fit(pil_img, (300, 220), Image.LANCZOS)
            
            # CRITICAL: Create image and keep strong reference
            CAM_CURRENT_IMAGE = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 220))
            
            # Update label - MUST happen before next iteration
            try:
                _source_label.configure(image=CAM_CURRENT_IMAGE, text="")
                _source_label.image = CAM_CURRENT_IMAGE  # Extra reference
            except Exception as e:
                print(f"Label update error: {e}")
    
    except Exception as e:
        print(f"Camera tick error: {e}")
    
    # Schedule next update
    if CAM_IS_RUNNING:
        CAM_AFTER_ID = _root.after(33, camera_feed_tick)

def do_capture():
    """Capture current frame"""
    from .file_handlers import update_status
    from .utils import render_image_preview
    from .pipeline import pipeline_process
    global CAM_FRAME_DATA
    
    if CAM_FRAME_DATA is None:
        update_status("❌ No frame to capture")
        return
    
    stop_camera_feed()
    path = os.path.join(tempfile.gettempdir(), f"roop_src_{int(time.time())}.png")
    
    try:
        cv2.imwrite(path, CAM_FRAME_DATA)
        roop.globals.source_path = path
        
        # Show preview
        preview = render_image_preview(path, (300, 220))
        _source_label.configure(image=preview, text="")
        _source_label.image = preview  # Keep reference
        
        if roop.globals.PIPELINE_ENABLED:
            _capture_btn.configure(state='disabled', text='⚡ Processing...', fg_color="#666")
            _root.after(500, pipeline_process)
        else:
            _capture_btn.configure(text='🔄 Re-capture', command=do_recapture, 
                                 state='normal', fg_color="#ff9100")
            update_status("✅ Captured!")
    except Exception as e:
        update_status(f"Capture error: {e}")
        do_recapture()

def do_recapture():
    """Restart camera feed"""
    from .file_handlers import update_status
    global CAM_FRAME_DATA, CAM_CURRENT_IMAGE
    
    if not _camera_switch_var.get():
        return
    
    CAM_FRAME_DATA = None
    CAM_CURRENT_IMAGE = None
    roop.globals.source_path = None
    
    _capture_btn.configure(text='📸 Capture Face', command=do_capture, 
                          state='normal', fg_color="#00bcd4")
    start_camera_feed()
    update_status("🔄 Camera restarted")

def enable_camera_for_pipeline():
    """Enable camera automatically for pipeline mode - FIXED for 2nd cycle"""
    from .file_handlers import update_status
    
    # 1. If Switch is OFF -> Turn it ON (First Cycle)
    if not _camera_switch_var.get():
        _camera_switch_var.set(True)
        update_status("🔄 Enabling camera for pipeline...")
        _root.after(200, handle_camera_toggle)
        
    # 2. If Switch is ON but Feed is STOPPED (Second Cycle Fix)
    elif not CAM_IS_RUNNING:
        update_status("🔄 Restarting camera feed for next cycle...")
        
        # Reset UI state for capture
        _capture_btn.configure(state='normal', text='📸 Capture Face', fg_color="#00bcd4")
        
        # Restart the visual feed loop
        start_camera_feed()

def get_camera_state():
    """Get current camera state"""
    return {
        'is_running': CAM_IS_RUNNING,
        'is_open': CAM_OBJECT is not None and CAM_OBJECT.isOpened()
    }