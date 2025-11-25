"""
UI utility functions
Contains reusable utility functions for the UI
"""

from typing import Tuple, Optional
import cv2
import customtkinter as ctk
from PIL import Image, ImageOps


def render_image_preview(path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    """Render an image preview at specified size"""
    try:
        img = ImageOps.fit(Image.open(path), size, Image.LANCZOS)
        return ctk.CTkImage(img, size=size)
    except Exception as e:
        print(f"Error rendering image preview: {e}")
        # Return a blank image on error
        blank_img = Image.new('RGB', size, color='#2b2b2b')
        return ctk.CTkImage(blank_img, size=size)


def render_video_preview(path: str, size: Tuple[int, int], frame_num: int = 0) -> Optional[ctk.CTkImage]:
    """Render a video frame preview at specified size"""
    try:
        cap = cv2.VideoCapture(path)
        if frame_num:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            img = ImageOps.fit(
                Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), 
                size, 
                Image.LANCZOS
            )
            return ctk.CTkImage(img, size=size)
    except Exception as e:
        print(f"Error rendering video preview: {e}")
    
    # Return a blank image on error
    blank_img = Image.new('RGB', size, color='#2b2b2b')
    return ctk.CTkImage(blank_img, size=size)