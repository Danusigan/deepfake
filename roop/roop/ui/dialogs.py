"""
Dialog windows - WITH ANIMATED GIF PREVIEWS IN SELECTION - FIXED
"""

from typing import Callable
import os
import cv2
import customtkinter as ctk
from PIL import Image, ImageOps
import roop.globals
from roop.utilities import is_image, is_video
from .utils import create_animated_gif_preview, stop_all_animations

COLOR_BG = "#0b101a"
COLOR_PINK = "#E91E63"
COLOR_PINK_HOVER = "#C2185B"

class TargetBrowserDialog(ctk.CTkToplevel):
    def __init__(self, master, categories: dict, callback, pipeline_mode=False):
        super().__init__(master)
        self.categories = categories
        self.callback = callback
        self.pipeline_mode = pipeline_mode
        
        self.title("Select Target")
        self.geometry("1400x800")
        self.state('zoomed')

        self.configure(fg_color=COLOR_BG)
        self.transient(master)
        self.grab_set()
        
        # Header
        header = ctk.CTkFrame(self, fg_color="#151923", height=50)
        header.pack(fill="x")
        self.title_lbl = ctk.CTkLabel(header, text="Select Target Category", 
                                     font=("Segoe UI", 18, "bold"), text_color=COLOR_PINK)
        self.title_lbl.pack(side="left", padx=20, pady=10)
        
        self.back_btn = ctk.CTkButton(header, text="⬅ Back", command=self.show_categories,
                                     width=60, fg_color="#333", hover_color="#444")
        
        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_categories()

    def show_categories(self):
        """Show categories - UPDATED FOR 4 CATEGORIES"""
        stop_all_animations()
        self.back_btn.pack_forget()
        for widget in self.container.winfo_children(): 
            widget.destroy()
        
        self.title_lbl.configure(text="Select Target Category")
        
        # Update grid for 4 columns (2x2 layout)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)
        
        icons = {
            "Male": "👨", 
            "Female": "👩", 
            "Children": "👶",
            "Trending": "🔥"  # Fire emoji for trending
        }
        
        # Position buttons in 2x2 grid
        positions = [
            (0, 0),  # Male - top left
            (0, 1),  # Female - top right
            (1, 0),  # Children - bottom left
            (1, 1)   # Trending - bottom right
        ]
        
        for idx, (name, path) in enumerate(self.categories.items()):
            row, col = positions[idx] if idx < len(positions) else (1, 1)
            
            btn = ctk.CTkButton(self.container, 
                               text=f"{icons.get(name, '📁')} {name}",
                               font=("Segoe UI", 24, "bold"),
                               fg_color=COLOR_PINK, 
                               hover_color=COLOR_PINK_HOVER,
                               corner_radius=15,
                               width=300, height=200,
                               command=lambda p=path, n=name: self.display_files(p, n))
            btn.grid(row=row, column=col, padx=30, pady=30, sticky="nsew")

    def display_files(self, targets_dir, category_name):
        """Display files - WITH ANIMATED GIF"""
        stop_all_animations()
        self.back_btn.pack(side="right", padx=10, pady=10)
        for widget in self.container.winfo_children(): 
            widget.destroy()
        
        # Update icon based on category
        icons = {
            "Male": "👨", 
            "Female": "👩", 
            "Children": "👶",
            "Trending": "🔥"
        }
        icon = icons.get(category_name, "📁")
        
        self.title_lbl.configure(text=f"{icon} Select: {category_name}")
        
        scroll_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        
        media_files = []
        if os.path.exists(targets_dir):
            for f in os.listdir(targets_dir):
                full = os.path.join(targets_dir, f)
                if is_image(full) or is_video(full): 
                    media_files.append(full)
        
        if not media_files:
            ctk.CTkLabel(scroll_frame, text="No files found in this category", 
                        font=("Segoe UI", 14), text_color="#8b949e").pack(pady=50)
            return
        
        # Use 4 columns so previews are larger and easier to see
        for i in range(4): 
            scroll_frame.grid_columnconfigure(i, weight=1)
        
        for idx, path in enumerate(media_files):
            r, c = divmod(idx, 4)
            
            card = ctk.CTkFrame(scroll_frame, fg_color="#1e232e", corner_radius=8)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            
            # Larger preview frames for better visibility
            preview_frame = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=6, 
                                        width=480, height=360)
            preview_frame.pack(padx=12, pady=12, fill="both", expand=True)
            preview_frame.pack_propagate(False)
            
            lbl = ctk.CTkLabel(preview_frame, text="")
            lbl.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Load larger preview immediately
            self.load_preview(path, (480, 360), lbl)
            
            filename = os.path.basename(path)
            if len(filename) > 40:
                filename = filename[:37] + "..."
            name_lbl = ctk.CTkLabel(card, text=filename, font=("Segoe UI", 13), 
                                   text_color="#8b949e")
            name_lbl.pack(pady=(0, 5))
            
            select_btn = ctk.CTkButton(card, text="Select", height=40,
                         fg_color=COLOR_PINK, hover_color=COLOR_PINK_HOVER,
                         font=("Segoe UI", 14, "bold"),
                         command=lambda p=path: self._select(p))
            select_btn.pack(fill="x", padx=5, pady=(0, 5))

    def load_preview(self, path, size, label):
        """Load preview - ANIMATED for GIF"""
        try:
            if self._is_gif(path):
                # CRITICAL: Create animated GIF preview
                success = create_animated_gif_preview(path, size, label, self)
                if not success:
                    # Fallback to static
                    img = self._get_static_preview(path, size)
                    label.configure(image=img)
                    label.image = img
            else:
                # Static preview
                img = self._get_static_preview(path, size)
                label.configure(image=img)
                label.image = img
        except Exception as e:
            print(f"[ERROR] Preview load: {e}")
            # Fallback blank
            blank = Image.new('RGB', size, '#000')
            img = ctk.CTkImage(blank, size=size)
            label.configure(image=img)
            label.image = img

    def _get_static_preview(self, path, size):
        """Get static preview"""
        try:
            if is_video(path):
                cap = cv2.VideoCapture(path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = ImageOps.contain(img, size, Image.LANCZOS)
                    return ctk.CTkImage(img, size=img.size)
            else:
                img = Image.open(path)
                img = ImageOps.contain(img, size, Image.LANCZOS)
                return ctk.CTkImage(img, size=img.size)
        except Exception as e:
            print(f"[ERROR] Static preview: {e}")
        
        blank = Image.new('RGB', size, '#000')
        return ctk.CTkImage(blank, size=size)

    def _is_gif(self, path):
        return path and path.lower().endswith('.gif')

    def _select(self, path):
        print(f"[DEBUG] Dialog select: {path}")
        stop_all_animations()
        self.callback(path)
        self.destroy()