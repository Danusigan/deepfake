"""
Preview window module
Contains preview window functionality
"""

import sys
import cv2
import customtkinter as ctk
from PIL import Image, ImageOps
import roop.globals
from roop.capturer import get_video_frame, get_video_frame_total
from roop.face_analyser import get_one_face
from roop.face_reference import get_face_reference, set_face_reference, clear_face_reference
from roop.predictor import predict_frame, clear_predictor
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import is_image, is_video

# Preview window components
PREVIEW = None
preview_label = None
preview_slider = None


def create_preview(parent):
    """Create preview window"""
    global PREVIEW, preview_label, preview_slider
    
    PREVIEW = ctk.CTkToplevel(parent)
    PREVIEW.withdraw()
    PREVIEW.protocol('WM_DELETE_WINDOW', toggle_preview)
    PREVIEW.resizable(False, False)
    
    preview_label = ctk.CTkLabel(PREVIEW, text=None)
    preview_label.pack(fill='both', expand=True)
    
    preview_slider = ctk.CTkSlider(PREVIEW, from_=0, to=0, command=lambda v: update_preview(v))
    
    PREVIEW.bind('<Up>', lambda e: update_face_reference(1))
    PREVIEW.bind('<Down>', lambda e: update_face_reference(-1))
    
    return PREVIEW


def close_preview():
    """Close preview window"""
    global PREVIEW
    if PREVIEW:
        try:
            PREVIEW.withdraw()
        except:
            pass


def toggle_preview():
    """Toggle preview window visibility"""
    global PREVIEW
    if not PREVIEW:
        return
    
    try:
        if PREVIEW.state() == 'normal':
            PREVIEW.unbind('<Right>')
            PREVIEW.unbind('<Left>')
            PREVIEW.withdraw()
            clear_predictor()
        elif roop.globals.source_path and roop.globals.target_path:
            init_preview()
            update_preview(roop.globals.reference_frame_number)
            PREVIEW.deiconify()
    except:
        pass


def init_preview():
    """Initialize preview window"""
    global PREVIEW
    if not PREVIEW:
        return
    
    PREVIEW.title('Preview')
    
    if is_image(roop.globals.target_path):
        preview_slider.pack_forget()
    
    if is_video(roop.globals.target_path):
        total = get_video_frame_total(roop.globals.target_path)
        if total > 0:
            PREVIEW.bind('<Right>', lambda e: update_frame(int(total / 20)))
            PREVIEW.bind('<Left>', lambda e: update_frame(int(total / -20)))
        preview_slider.configure(to=total)
        preview_slider.pack(fill='x')
        preview_slider.set(roop.globals.reference_frame_number)


def update_preview(frame_num: int = 0):
    """Update preview with processed frame"""
    if roop.globals.source_path and roop.globals.target_path:
        temp = get_video_frame(roop.globals.target_path, frame_num)
        if predict_frame(temp):
            sys.exit()
        
        src_face = get_one_face(cv2.imread(roop.globals.source_path))
        
        if not get_face_reference():
            ref = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            set_face_reference(get_one_face(ref, roop.globals.reference_face_position))
        
        for proc in get_frame_processors_modules(roop.globals.frame_processors):
            temp = proc.process_frame(src_face, get_face_reference(), temp)
        
        img = ImageOps.contain(
            Image.fromarray(cv2.cvtColor(temp, cv2.COLOR_BGR2RGB)), 
            (1200, 700), 
            Image.LANCZOS
        )
        preview_label.configure(image=ctk.CTkImage(img, size=img.size))


def update_face_reference(steps: int):
    """Update face reference position"""
    clear_face_reference()
    roop.globals.reference_face_position += steps
    roop.globals.reference_frame_number = int(preview_slider.get())
    update_preview(roop.globals.reference_frame_number)


def update_frame(steps: int):
    """Update preview frame"""
    preview_slider.set(preview_slider.get() + steps)
    update_preview(preview_slider.get())