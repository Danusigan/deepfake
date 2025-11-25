"""
Camera handling module
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
CAM_IMAGE_REF = None

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
    global CAM_IS_RUNNING, CAM_AFTER_ID
    CAM_IS_RUNNING = False
    if CAM_AFTER_ID is not None:
        try:
            _root.after_cancel(CAM_AFTER_ID)
        except:
            pass
        CAM_AFTER_ID = None

def release_camera():
    global CAM_OBJECT, CAM_FRAME_DATA
    stop_camera_feed()
    if CAM_OBJECT is not None:
        try:
            CAM_OBJECT.release()
        except:
            pass
        CAM_OBJECT = None
    CAM_FRAME_DATA = None

def destroy_camera():
    release_camera()
    try:
        cv2.destroyAllWindows()
    except:
        pass

def open_camera():
    global CAM_OBJECT
    release_camera()
    time.sleep(0.3)
    CAM_OBJECT = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if CAM_OBJECT is None or not CAM_OBJECT.isOpened():
        CAM_OBJECT = cv2.VideoCapture(0)
    
    if CAM_OBJECT is not None and CAM_OBJECT.isOpened():
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ret, frame = CAM_OBJECT.read()
        if ret:
            return True
    release_camera()
    return False

def handle_camera_toggle():
    from .file_handlers import update_status
    global CAM_IS_RUNNING
    
    if _camera_switch_var.get():
        update_status("Opening camera...")
        _root.update()
        if open_camera():
            CAM_IS_RUNNING = True
            if not roop.globals.PIPELINE_ENABLED:
                roop.globals.source_path = None
            
            _capture_btn.configure(state='normal', text='📸 Capture Face', fg_color="#00e5ff")
            start_camera_feed()
            update_status("Camera ON")
        else:
            _camera_switch_var.set(False)
            _capture_btn.configure(state='disabled')
            update_status("Cannot open camera!")
    else:
        release_camera()
        _capture_btn.configure(state='disabled', text='📸 Capture Face', fg_color="#00e5ff")
        if not roop.globals.source_path:
            _source_label.configure(image=None, text="Drag & Drop Image\n\n📸\n\nOr toggle camera ON")
        update_status("Camera OFF")

def start_camera_feed():
    global CAM_IS_RUNNING
    CAM_IS_RUNNING = True
    _root.after(100, camera_feed_tick)

def camera_feed_tick():
    global CAM_AFTER_ID, CAM_FRAME_DATA, CAM_IMAGE_REF
    
    if not CAM_IS_RUNNING: return
    
    if CAM_OBJECT is None or not CAM_OBJECT.isOpened():
        if open_camera():
            CAM_AFTER_ID = _root.after(50, camera_feed_tick)
        else:
            _camera_switch_var.set(False)
        return
    
    try:
        ret, frame = CAM_OBJECT.read()
        if ret and frame is not None:
            CAM_FRAME_DATA = frame.copy()
            # Crop/Resize for UI
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = ImageOps.fit(pil_img, (300, 220), Image.LANCZOS)
            CAM_IMAGE_REF = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(300, 220))
            _source_label.configure(image=CAM_IMAGE_REF, text="")
    except Exception:
        pass
    
    if CAM_IS_RUNNING:
        CAM_AFTER_ID = _root.after(30, camera_feed_tick)

def do_capture():
    from .file_handlers import update_status
    from .utils import render_image_preview
    from .pipeline import pipeline_process
    global CAM_FRAME_DATA
    
    if CAM_FRAME_DATA is None: return
    
    stop_camera_feed()
    path = os.path.join(tempfile.gettempdir(), f"roop_src_{int(time.time())}.png")
    
    try:
        cv2.imwrite(path, CAM_FRAME_DATA)
        roop.globals.source_path = path
        _source_label.configure(image=render_image_preview(path, (300, 220)), text="")
        
        if roop.globals.PIPELINE_ENABLED:
            _capture_btn.configure(state='disabled', text='⚡ Processing...')
            _root.after(500, pipeline_process)
        else:
            _capture_btn.configure(text='🔄 Re-capture', command=do_recapture, fg_color="#ff9100")
            update_status("Captured!")
    except Exception as e:
        do_recapture()

def do_recapture():
    from .file_handlers import update_status
    global CAM_FRAME_DATA
    if not _camera_switch_var.get(): return
    CAM_FRAME_DATA = None
    roop.globals.source_path = None
    _capture_btn.configure(text='📸 Capture Face', command=do_capture, fg_color="#00e5ff")
    start_camera_feed()

def get_camera_state():
    return {'is_running': CAM_IS_RUNNING, 'is_open': CAM_OBJECT is not None and CAM_OBJECT.isOpened()}