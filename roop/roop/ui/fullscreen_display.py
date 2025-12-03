"""
Fullscreen display module - Display processed output in fullscreen
Shows images, videos, or GIFs in fullscreen after processing completes
"""

import tkinter as tk
import cv2
from PIL import Image, ImageTk
import os
from roop.utilities import is_image, is_video
from .utils import stop_all_animations
from pathlib import Path
import sys

# Global fullscreen window reference
FULLSCREEN_WINDOW = None
ANIMATION_STOP_FLAG = False


def show_output_fullscreen(file_path: str, parent_root=None):
    """
    Display output image/video/gif in fullscreen window.

    This function resolves the given path to an absolute path (helpful when files
    are saved under `targets/Outputs`). If a `parent_root` is supplied (the
    main application root), a `Toplevel` window is created and attached to it
    (this avoids creating multiple independent `Tk()` roots which can cause
    PhotoImage issues). The window is forced to render before PhotoImage is
    created to prevent the "pyimageX doesn't exist" error.
    """
    global FULLSCREEN_WINDOW, ANIMATION_STOP_FLAG

    # Resolve to absolute path
    try:
        resolved = str(Path(file_path).expanduser().resolve())
    except Exception:
        resolved = os.path.abspath(file_path)

    print(f"[DEBUG] show_output_fullscreen: requested='{file_path}' resolved='{resolved}'")

    if not os.path.exists(resolved):
        print(f"[ERROR] File not found: {resolved}")
        _show_error_message(f"File not found: {resolved}")
        return

    # Reset animation flag
    ANIMATION_STOP_FLAG = False

    # Create a window attached to the main root when provided
    try:
        if parent_root:
            window = tk.Toplevel(master=parent_root)
        else:
            window = tk.Tk()

        window.attributes('-fullscreen', True)
        window.configure(bg='#000000')
        window.focus_force()

        # store main reference before creating widgets so helpers can use it
        FULLSCREEN_WINDOW = window

        # Ensure window is present before creating PhotoImage
        window.update_idletasks()
        window.update()

        # Display content
        if resolved.lower().endswith('.gif'):
            _show_gif_fullscreen(resolved)
        elif is_video(resolved):
            _show_video_fullscreen(resolved)
        elif is_image(resolved):
            _show_image_fullscreen(resolved)
        else:
            _show_error_message("Unsupported file format")
            return

        print("[DEBUG] Content displayed successfully")

    except Exception as e:
        print(f"[ERROR] Fullscreen display error: {e}")
        import traceback
        traceback.print_exc()


def _show_image_fullscreen(file_path: str):
    """Display static image in fullscreen"""
    print(f"[DEBUG] _show_image_fullscreen: {file_path}")
    
    try:
        # Get screen dimensions
        screen_width = FULLSCREEN_WINDOW.winfo_screenwidth()
        screen_height = FULLSCREEN_WINDOW.winfo_screenheight()
        print(f"[DEBUG] Screen size: {screen_width}x{screen_height}")
        
        # Load image
        img = Image.open(file_path)
        print(f"[DEBUG] Image loaded: {img.mode} {img.size}")
        
        # Convert to RGB
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (0, 0, 0))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to fit screen maintaining aspect ratio
        img_w, img_h = img.size
        screen_ratio = screen_width / screen_height
        img_ratio = img_w / img_h
        
        if img_ratio > screen_ratio:
            # Image is wider
            new_w = screen_width
            new_h = int(screen_width / img_ratio)
        else:
            # Image is taller
            new_h = screen_height
            new_w = int(screen_height * img_ratio)
        
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print(f"[DEBUG] Image resized to: {new_w}x{new_h}")
        
        # Create PhotoImage
        photo = ImageTk.PhotoImage(img)
        print(f"[DEBUG] PhotoImage created")
        
        # Create label for image
        label = tk.Label(FULLSCREEN_WINDOW, image=photo, bg='#000000')
        label.image = photo  # Keep reference to prevent garbage collection
        label.pack(fill=tk.BOTH, expand=True)
        print("[DEBUG] Image label packed")
        
        # Add instructions at bottom
        instructions = tk.Label(
            FULLSCREEN_WINDOW,
            text="Press ESC or Q to close",
            bg='#000000',
            fg='#888888',
            font=('Arial', 12)
        )
        instructions.pack(side=tk.BOTTOM, pady=20)
        
        # Store reference in window
        FULLSCREEN_WINDOW.current_image = photo
        
        print("[DEBUG] Image displayed successfully")
        
    except Exception as e:
        print(f"[ERROR] Image display error: {e}")
        import traceback
        traceback.print_exc()
        _show_error_message(f"Error: {str(e)}")


def _show_video_fullscreen(file_path: str):
    """Display video in fullscreen"""
    print(f"[DEBUG] _show_video_fullscreen: {file_path}")
    
    try:
        cap = cv2.VideoCapture(file_path)
        
        if not cap.isOpened():
            _show_error_message("Could not open video file")
            return
        
        screen_width = FULLSCREEN_WINDOW.winfo_screenwidth()
        screen_height = FULLSCREEN_WINDOW.winfo_screenheight()
        
        # Get FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        frame_delay = int(1000 / fps)
        
        # Create label for video
        video_label = tk.Label(FULLSCREEN_WINDOW, bg='#000000')
        video_label.pack(fill=tk.BOTH, expand=True)
        
        # Add instructions
        instructions = tk.Label(
            FULLSCREEN_WINDOW,
            text="Press ESC or Q to close",
            bg='#000000',
            fg='#888888',
            font=('Arial', 12)
        )
        instructions.pack(side=tk.BOTTOM, pady=20)
        
        # Store video state
        video_state = {
            'cap': cap,
            'label': video_label,
            'frame_delay': frame_delay,
            'screen_width': screen_width,
            'screen_height': screen_height
        }
        
        # Start playing
        _play_video_frame(video_state)
        
        print("[DEBUG] Video playback started")
        
    except Exception as e:
        print(f"[ERROR] Video display error: {e}")
        import traceback
        traceback.print_exc()
        _show_error_message(f"Error: {str(e)}")


def _play_video_frame(video_state):
    """Play next video frame"""
    global ANIMATION_STOP_FLAG
    
    if ANIMATION_STOP_FLAG or not FULLSCREEN_WINDOW:
        video_state['cap'].release()
        return
    
    try:
        ret, frame = video_state['cap'].read()
        
        if not ret:
            video_state['cap'].release()
            return
        
        # Convert and resize frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame_rgb.shape[:2]
        
        aspect_ratio = w / h
        screen_ratio = video_state['screen_width'] / video_state['screen_height']
        
        if aspect_ratio > screen_ratio:
            new_w = video_state['screen_width']
            new_h = int(video_state['screen_width'] / aspect_ratio)
        else:
            new_h = video_state['screen_height']
            new_w = int(video_state['screen_height'] * aspect_ratio)
        
        frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
        
        # Convert to PhotoImage
        pil_img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(pil_img)
        
        # Update label
        video_state['label'].config(image=photo)
        video_state['label'].image = photo
        
        # Schedule next frame
        if FULLSCREEN_WINDOW:
            FULLSCREEN_WINDOW.after(video_state['frame_delay'], 
                                   lambda: _play_video_frame(video_state))
        
    except Exception as e:
        print(f"[ERROR] Video frame error: {e}")
        video_state['cap'].release()


def _show_gif_fullscreen(file_path: str):
    """Display animated GIF in fullscreen"""
    print(f"[DEBUG] _show_gif_fullscreen: {file_path}")
    
    global ANIMATION_STOP_FLAG
    ANIMATION_STOP_FLAG = False
    
    try:
        screen_width = FULLSCREEN_WINDOW.winfo_screenwidth()
        screen_height = FULLSCREEN_WINDOW.winfo_screenheight()
        
        # Open GIF
        gif_image = Image.open(file_path)
        
        # Load all frames
        frames = []
        durations = []
        
        frame_index = 0
        try:
            while True:
                duration = gif_image.info.get('duration', 100)
                durations.append(max(duration, 50))
                
                frame = gif_image.convert('RGB')
                frame.thumbnail((screen_width, screen_height), Image.LANCZOS)
                frames.append(frame)
                
                frame_index += 1
                gif_image.seek(frame_index)
        except EOFError:
            pass
        
        if not frames:
            _show_error_message("Could not load GIF frames")
            return
        
        print(f"[DEBUG] Loaded {len(frames)} GIF frames")
        
        # Create label for GIF
        gif_label = tk.Label(FULLSCREEN_WINDOW, bg='#000000')
        gif_label.pack(fill=tk.BOTH, expand=True)
        
        # Add instructions
        instructions = tk.Label(
            FULLSCREEN_WINDOW,
            text="Press ESC or Q to close",
            bg='#000000',
            fg='#888888',
            font=('Arial', 12)
        )
        instructions.pack(side=tk.BOTTOM, pady=20)
        
        # Store GIF state
        gif_state = {
            'frames': frames,
            'durations': durations,
            'current_frame': 0,
            'label': gif_label
        }
        
        # Start animation
        _play_gif_frame(gif_state)
        
        print("[DEBUG] GIF animation started")
        
    except Exception as e:
        print(f"[ERROR] GIF display error: {e}")
        import traceback
        traceback.print_exc()
        _show_error_message(f"Error: {str(e)}")


def _play_gif_frame(gif_state):
    """Play next GIF frame"""
    global ANIMATION_STOP_FLAG
    
    if ANIMATION_STOP_FLAG or not FULLSCREEN_WINDOW:
        return
    
    try:
        frame = gif_state['frames'][gif_state['current_frame']]
        duration = gif_state['durations'][gif_state['current_frame']]
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(frame)
        
        # Update label
        gif_state['label'].config(image=photo)
        gif_state['label'].image = photo
        
        # Move to next frame
        gif_state['current_frame'] = (gif_state['current_frame'] + 1) % len(gif_state['frames'])
        
        # Schedule next frame
        if FULLSCREEN_WINDOW:
            FULLSCREEN_WINDOW.after(duration, lambda: _play_gif_frame(gif_state))
        
    except Exception as e:
        print(f"[ERROR] GIF frame error: {e}")


def _show_error_message(message: str):
    """Display error message"""
    try:
        error_label = tk.Label(
            FULLSCREEN_WINDOW,
            text=message,
            bg='#000000',
            fg='#ff0055',
            font=('Arial', 20),
            wraplength=800
        )
        error_label.pack(expand=True)
        
        instructions = tk.Label(
            FULLSCREEN_WINDOW,
            text="Press ESC or Q to close",
            bg='#000000',
            fg='#888888',
            font=('Arial', 12)
        )
        instructions.pack(side=tk.BOTTOM, pady=20)
        
    except Exception as e:
        print(f"[ERROR] Error message display: {e}")


def close_fullscreen():
    """Close fullscreen window"""
    global FULLSCREEN_WINDOW, ANIMATION_STOP_FLAG
    
    print("[DEBUG] Closing fullscreen window")
    
    ANIMATION_STOP_FLAG = True
    stop_all_animations()
    
    if FULLSCREEN_WINDOW:
        try:
            FULLSCREEN_WINDOW.destroy()
        except:
            pass
        FULLSCREEN_WINDOW = None
    
    print("[DEBUG] Fullscreen window closed")
