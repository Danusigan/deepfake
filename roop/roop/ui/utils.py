"""
UI utility functions - WITH ANIMATED GIF SUPPORT
Contains reusable utility functions for the UI
"""

from typing import Tuple, Optional, List
import cv2
import customtkinter as ctk
from PIL import Image, ImageOps, ImageSequence
import threading


def render_image_preview(path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    """Render an image preview at specified size"""
    try:
        img = ImageOps.fit(Image.open(path), size, Image.LANCZOS)
        return ctk.CTkImage(img, size=size)
    except Exception as e:
        print(f"Error rendering image preview: {e}")
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
    
    blank_img = Image.new('RGB', size, color='#2b2b2b')
    return ctk.CTkImage(blank_img, size=size)


class AnimatedGIF:
    """Class to handle animated GIF playback in CTkLabel - OPTIMIZED"""
    
    def __init__(self, gif_path: str, size: Tuple[int, int], label: ctk.CTkLabel, root):
        self.gif_path = gif_path
        self.size = size
        self.label = label
        self.root = root
        self.frames = []
        self.current_frame = 0
        self.is_playing = False
        self.delay = 100
        self.after_id = None
        
        self.load_frames()
    
    def load_frames(self):
        """Load all frames from GIF - OPTIMIZED"""
        try:
            img = Image.open(self.gif_path)
            
            # Get frame delay
            try:
                self.delay = img.info.get('duration', 100)
                if self.delay < 30:
                    self.delay = 30
            except:
                self.delay = 100
            
            # OPTIMIZATION: Limit number of frames for very long GIFs
            frame_count = 0
            max_frames = 100  # Limit to 100 frames for UI responsiveness
            
            # Extract frames
            for frame in ImageSequence.Iterator(img):
                if frame_count >= max_frames:
                    print(f"[DEBUG] GIF has {frame_count}+ frames, limiting to {max_frames} for preview")
                    break
                
                # Resize frame using CONTAIN to show full image
                frame_resized = ImageOps.contain(frame.convert('RGB'), self.size, Image.LANCZOS)
                # Convert to CTkImage
                ctk_frame = ctk.CTkImage(frame_resized, size=frame_resized.size)
                self.frames.append(ctk_frame)
                frame_count += 1
            
            print(f"[DEBUG] Loaded {len(self.frames)} frames from GIF")
        except Exception as e:
            print(f"Error loading GIF frames: {e}")
    
    def play(self):
        """Start playing the GIF animation"""
        if len(self.frames) == 0:
            print("[DEBUG] No frames to play")
            return False
        
        self.is_playing = True
        self.animate()
        return True
    
    def stop(self):
        """Stop the animation"""
        self.is_playing = False
        if self.after_id:
            try:
                self.root.after_cancel(self.after_id)
            except:
                pass
            self.after_id = None
    
    def animate(self):
        """Animation loop"""
        if not self.is_playing or len(self.frames) == 0:
            return
        
        try:
            # Update label with current frame
            self.label.configure(image=self.frames[self.current_frame], text="")
            
            # Move to next frame
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            # Schedule next frame
            self.after_id = self.root.after(self.delay, self.animate)
        except Exception as e:
            print(f"Animation error: {e}")
            self.is_playing = False


# Global storage for animated GIF players
_gif_players = {}


def create_animated_gif_preview(gif_path: str, size: Tuple[int, int], 
                                label: ctk.CTkLabel, root) -> bool:
    """
    Create and play an animated GIF preview in a CTkLabel
    Returns True if successful, False otherwise
    """
    global _gif_players
    
    try:
        # Stop any existing animation for this label
        label_id = id(label)
        if label_id in _gif_players:
            _gif_players[label_id].stop()
            del _gif_players[label_id]
        
        # Create new animated GIF player
        gif_player = AnimatedGIF(gif_path, size, label, root)
        
        # Start playing
        if gif_player.play():
            # Store reference
            _gif_players[label_id] = gif_player
            print(f"[DEBUG] Started GIF animation for label {label_id}")
            return True
        else:
            print(f"[DEBUG] Failed to start GIF animation")
            return False
    
    except Exception as e:
        print(f"Error creating animated GIF preview: {e}")
        import traceback
        traceback.print_exc()
        return False


def stop_all_animations():
    """Stop all active GIF animations"""
    global _gif_players
    for player in _gif_players.values():
        player.stop()
    _gif_players.clear()
    print("[DEBUG] Stopped all GIF animations")


def render_gif_preview(path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    """Render first frame of GIF as static preview (fallback)"""
    try:
        img = Image.open(path)
        img.seek(0)
        img_resized = ImageOps.contain(img.convert('RGB'), size, Image.LANCZOS)
        return ctk.CTkImage(img_resized, size=img_resized.size)
    except Exception as e:
        print(f"Error rendering GIF preview: {e}")
        blank_img = Image.new('RGB', size, color='#2b2b2b')
        return ctk.CTkImage(blank_img, size=size)