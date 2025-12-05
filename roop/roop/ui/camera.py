"""
Camera handling module - With Android Phone Camera Support
Supports both regular webcam and Android phone via IP Webcam
"""

import cv2
import time
import os
import tempfile
from PIL import Image, ImageOps
import customtkinter as ctk
import roop.globals
import requests
import numpy as np
from typing import Optional

# Camera state
CAM_OBJECT = None
CAM_IS_RUNNING = False
CAM_AFTER_ID = None
CAM_FRAME_DATA = None
CAM_CURRENT_IMAGE = None
CAM_TYPE = "webcam"  # "webcam" or "ip_webcam"
IP_WEBCAM_URL = None

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
    global CAM_OBJECT, CAM_FRAME_DATA, CAM_CURRENT_IMAGE, IP_WEBCAM_URL
    
    stop_camera_feed()
    
    CAM_CURRENT_IMAGE = None
    CAM_FRAME_DATA = None
    
    if CAM_TYPE == "webcam" and CAM_OBJECT is not None:
        try:
            CAM_OBJECT.release()
        except:
            pass
        finally:
            CAM_OBJECT = None
    elif CAM_TYPE == "ip_webcam":
        IP_WEBCAM_URL = None
    
    time.sleep(0.3)
    try:
        cv2.destroyAllWindows()
    except:
        pass

def destroy_camera():
    """Complete camera cleanup"""
    release_camera()

def open_camera():
    """Open camera with proper initialization (supports both webcam and IP webcam)"""
    global CAM_OBJECT, CAM_TYPE, IP_WEBCAM_URL
    
    # First, try to connect to IP Webcam (if configured)
    ip_url = detect_ip_webcam()
    
    if ip_url:
        # Use IP Webcam
        CAM_TYPE = "ip_webcam"
        IP_WEBCAM_URL = ip_url
        
        # Test connection
        if test_ip_webcam_connection():
            return True
        else:
            from .file_handlers import update_status
            update_status("❌ Cannot connect to IP Webcam")
    
    # Fallback to regular webcam
    CAM_TYPE = "webcam"
    
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
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
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

def detect_ip_webcam() -> Optional[str]:
    """
    Auto-detect IP Webcam on local network
    Checks common IP ranges and ports
    """
    # Check if user has configured IP manually
    config_file = os.path.join(os.path.dirname(__file__), 'ip_webcam_config.txt')
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                ip = f.read().strip()
                if ip:
                    return f"http://{ip}:8080"
        except:
            pass
    
    # Try to auto-detect (optional - may take time)
    # For now, return None to skip auto-detection
    return None

def test_ip_webcam_connection() -> bool:
    """Test if IP Webcam is reachable"""
    if not IP_WEBCAM_URL:
        return False
    
    try:
        response = requests.get(f"{IP_WEBCAM_URL}/shot.jpg", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_ip_webcam_frame() -> Optional[np.ndarray]:
    """Get frame from IP Webcam"""
    if not IP_WEBCAM_URL:
        return None
    
    try:
        # Get JPEG frame
        response = requests.get(f"{IP_WEBCAM_URL}/shot.jpg", timeout=1)
        
        if response.status_code == 200:
            # Decode JPEG to numpy array
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return frame
    except Exception as e:
        print(f"IP Webcam frame error: {e}")
    
    return None

def handle_camera_toggle():
    """Handle camera on/off toggle"""
    from .file_handlers import update_status
    global CAM_IS_RUNNING
    
    if _camera_switch_var.get():
        # Prompt user for camera type
        show_camera_selection_dialog()
    else:
        release_camera()
        _capture_btn.configure(state='disabled', text='📸 Capture Face')
        if not roop.globals.source_path:
            _source_label.configure(image='', text="Drag & Drop Image\nor Click to Select\n\nOr toggle camera ON")
        update_status("Camera OFF")

def show_camera_selection_dialog():
    """Show dialog to select camera type"""
    from .file_handlers import update_status
    
    dialog = ctk.CTkToplevel(_root)
    dialog.title("Select Camera Source")
    dialog.geometry("400x250")
    dialog.configure(fg_color="#0b0f19")
    dialog.transient(_root)
    dialog.grab_set()
    
    ctk.CTkLabel(dialog, text="Choose Camera Source", 
                font=("Segoe UI", 16, "bold")).pack(pady=20)
    
    def use_webcam():
        global CAM_TYPE
        CAM_TYPE = "webcam"
        dialog.destroy()
        start_camera_with_type()
    
    def use_ip_webcam():
        dialog.destroy()
        show_ip_config_dialog()
    
    ctk.CTkButton(dialog, text="💻 Use Laptop Webcam", 
                 command=use_webcam, height=40,
                 fg_color="#00bcd4", hover_color="#0097a7").pack(pady=10, padx=40, fill="x")
    
    ctk.CTkButton(dialog, text="📱 Use Android Phone (IP Webcam)", 
                 command=use_ip_webcam, height=40,
                 fg_color="#E91E63", hover_color="#C2185B").pack(pady=10, padx=40, fill="x")
    
    ctk.CTkButton(dialog, text="❌ Cancel", 
                 command=lambda: (dialog.destroy(), _camera_switch_var.set(False)),
                 fg_color="#333", hover_color="#444").pack(pady=10)

def show_ip_config_dialog():
    """Show dialog to configure IP Webcam"""
    from .file_handlers import update_status
    global IP_WEBCAM_URL, CAM_TYPE
    
    dialog = ctk.CTkToplevel(_root)
    dialog.title("Configure IP Webcam")
    dialog.geometry("500x300")
    dialog.configure(fg_color="#0b0f19")
    dialog.transient(_root)
    dialog.grab_set()
    
    ctk.CTkLabel(dialog, text="📱 Android Phone IP Webcam Setup", 
                font=("Segoe UI", 16, "bold")).pack(pady=15)
    
    info_text = """1. Install 'IP Webcam' app from Play Store
2. Open app and tap 'Start Server'
3. Note the IP address shown (e.g., 192.168.1.100)
4. Enter the IP below"""
    
    ctk.CTkLabel(dialog, text=info_text, justify="left",
                font=("Segoe UI", 11)).pack(pady=10)
    
    ctk.CTkLabel(dialog, text="Phone IP Address:", 
                font=("Segoe UI", 12, "bold")).pack(pady=5)
    
    ip_entry = ctk.CTkEntry(dialog, width=300, height=35,
                           placeholder_text="10.50.60.130 or http://10.50.60.130:8080")
    ip_entry.pack(pady=5)
    
    # Try to load saved IP
    config_file = os.path.join(os.path.dirname(__file__), 'ip_webcam_config.txt')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                saved_ip = f.read().strip()
                if saved_ip:
                    ip_entry.insert(0, saved_ip)
        except:
            pass
    
    status_lbl = ctk.CTkLabel(dialog, text="", font=("Segoe UI", 10))
    status_lbl.pack(pady=5)
    
    def connect():
        global IP_WEBCAM_URL, CAM_TYPE
        ip = ip_entry.get().strip()
        
        if not ip:
            status_lbl.configure(text="❌ Please enter IP address", text_color="#ff5252")
            return
        
        # Parse IP - handle full URL or just IP
        if ip.startswith('http://'):
            # Full URL provided
            IP_WEBCAM_URL = ip.rstrip('/')
        elif ':' in ip:
            # IP with port (e.g., 10.50.60.130:8080)
            IP_WEBCAM_URL = f"http://{ip}"
        else:
            # Just IP (e.g., 10.50.60.130)
            IP_WEBCAM_URL = f"http://{ip}:8080"
        
        # Save for future use (save clean IP only)
        clean_ip = IP_WEBCAM_URL.replace('http://', '').replace(':8080', '')
        try:
            with open(config_file, 'w') as f:
                f.write(clean_ip)
        except:
            pass
        
        CAM_TYPE = "ip_webcam"
        
        status_lbl.configure(text="🔄 Connecting...", text_color="#00bcd4")
        dialog.update()
        
        if test_ip_webcam_connection():
            status_lbl.configure(text="✅ Connected!", text_color="#00e676")
            dialog.after(1000, dialog.destroy)
            dialog.after(1100, start_camera_with_type)
        else:
            status_lbl.configure(text="❌ Cannot connect. Check IP and app.", 
                               text_color="#ff5252")
            IP_WEBCAM_URL = None
    
    ctk.CTkButton(dialog, text="🔗 Connect", command=connect,
                 fg_color="#E91E63", hover_color="#C2185B",
                 height=40, width=200).pack(pady=15)

def start_camera_with_type():
    """Start camera based on selected type"""
    from .file_handlers import update_status
    global CAM_IS_RUNNING
    
    if CAM_TYPE == "ip_webcam":
        update_status("📱 Connecting to phone camera...")
    else:
        update_status("💻 Opening laptop camera...")
    
    _root.update()
    
    if open_camera():
        CAM_IS_RUNNING = True
        _capture_btn.configure(state='normal', text='📸 Capture Face', fg_color="#00bcd4")
        start_camera_feed()
        
        if CAM_TYPE == "ip_webcam":
            update_status("✅ Phone camera connected - HD quality!")
        else:
            update_status("✅ Laptop camera ON")
    else:
        _camera_switch_var.set(False)
        _capture_btn.configure(state='disabled')
        update_status("❌ Cannot open camera!")

def start_camera_feed():
    """Start displaying camera feed"""
    global CAM_IS_RUNNING
    if CAM_IS_RUNNING and CAM_AFTER_ID is not None:
        return
    CAM_IS_RUNNING = True
    _root.after(150, camera_feed_tick)

def camera_feed_tick():
    """Update camera feed display - supports both webcam and IP webcam"""
    global CAM_AFTER_ID, CAM_FRAME_DATA, CAM_CURRENT_IMAGE
    
    if not CAM_IS_RUNNING:
        return
    
    frame = None
    
    try:
        if CAM_TYPE == "ip_webcam":
            # Get frame from IP Webcam
            frame = get_ip_webcam_frame()
            
            if frame is None:
                # Connection lost
                from .file_handlers import update_status
                update_status("❌ Phone camera disconnected")
                _camera_switch_var.set(False)
                return
        else:
            # Regular webcam
            if not CAM_OBJECT or not CAM_OBJECT.isOpened():
                _camera_switch_var.set(False)
                from .file_handlers import update_status
                update_status("Camera disconnected")
                return
            
            ret, frame = CAM_OBJECT.read()
            if not ret or frame is None:
                return
        
        if frame is not None and frame.size > 0:
            # Store for capture
            CAM_FRAME_DATA = frame.copy()
            
            # Process for display
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img = ImageOps.fit(pil_img, (300, 220), Image.LANCZOS)
            
            CAM_CURRENT_IMAGE = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, 
                                            size=(300, 220))
            
            try:
                _source_label.configure(image=CAM_CURRENT_IMAGE, text="")
                _source_label.image = CAM_CURRENT_IMAGE
            except Exception as e:
                print(f"Label update error: {e}")
    
    except Exception as e:
        print(f"Camera tick error: {e}")
    
    if CAM_IS_RUNNING:
        # Adjust delay based on camera type
        delay = 50 if CAM_TYPE == "ip_webcam" else 33
        CAM_AFTER_ID = _root.after(delay, camera_feed_tick)

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
        
        preview = render_image_preview(path, (300, 220))
        _source_label.configure(image=preview, text="")
        _source_label.image = preview
        
        if roop.globals.PIPELINE_ENABLED:
            _capture_btn.configure(state='disabled', text='⚡ Processing...', fg_color="#666")
            _root.after(500, pipeline_process)
        else:
            _capture_btn.configure(text='🔄 Re-capture', command=do_recapture, 
                                 state='normal', fg_color="#ff9100")
            
            if CAM_TYPE == "ip_webcam":
                update_status("✅ HD photo captured from phone!")
            else:
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
    """Enable camera automatically for pipeline mode"""
    from .file_handlers import update_status
    
    if not _camera_switch_var.get():
        _camera_switch_var.set(True)
        update_status("🔄 Enabling camera for pipeline...")
        _root.after(200, handle_camera_toggle)
    elif not CAM_IS_RUNNING:
        update_status("🔄 Restarting camera feed for next cycle...")
        _capture_btn.configure(state='normal', text='📸 Capture Face', fg_color="#00bcd4")
        start_camera_feed()

def get_camera_state():
    """Get current camera state"""
    is_open = False
    
    if CAM_TYPE == "ip_webcam":
        is_open = IP_WEBCAM_URL is not None
    else:
        is_open = CAM_OBJECT is not None and CAM_OBJECT.isOpened()
    
    return {
        'is_running': CAM_IS_RUNNING,
        'is_open': is_open,
        'type': CAM_TYPE
    }