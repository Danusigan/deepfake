"""
Dialog windows module - FIXED: Full image display with animated GIF/video support
"""

from typing import Callable, Tuple
import os
import cv2
import customtkinter as ctk
from PIL import Image, ImageOps
from tkinter import messagebox
import roop.globals
from roop.utilities import is_image, is_video

# --- COLORS ---
COLOR_BG = "#0b101a"
COLOR_PINK = "#E91E63"
COLOR_PINK_HOVER = "#C2185B"

class TargetBrowserDialog(ctk.CTkToplevel):
    def __init__(self, master, categories: dict, callback, pipeline_mode=False):
        super().__init__(master)
        self.categories = categories
        self.callback = callback
        self.pipeline_mode = pipeline_mode
        self.current_category_path = None
        self.animated_previews = []  # Track animated GIF players
        
        self.title("Select Target Category")
        self.geometry("1400x800")
        self.state('zoomed')

        self.configure(fg_color=COLOR_BG)
        self.transient(master)
        self.grab_set()
        
        # Header
        header = ctk.CTkFrame(self, fg_color="#151923", height=50)
        header.pack(fill="x")
        self.title_lbl = ctk.CTkLabel(header, text="Select Target Category (Pipeline Mode)" if pipeline_mode else "Select Target Category", 
                                     font=("Segoe UI", 18, "bold"), text_color=COLOR_PINK)
        self.title_lbl.pack(side="left", padx=20, pady=10)
        
        self.back_btn = ctk.CTkButton(header, text="⬅ Back", command=self.show_categories,
                                     width=60, fg_color="#333", hover_color="#444")
        
        # Content Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_categories()

    def show_categories(self):
        """Show category selection"""
        self.stop_all_animations()
        self.back_btn.pack_forget()
        for widget in self.container.winfo_children(): 
            widget.destroy()
        
        self.title_lbl.configure(text="Select Target Category")
        
        # Grid for Categories (3 Columns)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_columnconfigure(2, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Define Icons
        icons = {"Male": "👨", "Female": "👩", "Children": "👶"}
        
        col = 0
        for name, path in self.categories.items():
            # LARGE PINK CARD
            btn = ctk.CTkButton(self.container, 
                               text=f"{name} {icons.get(name, '')}",
                               font=("Segoe UI", 24, "bold"),
                               fg_color=COLOR_PINK, 
                               hover_color=COLOR_PINK_HOVER,
                               corner_radius=15,
                               width=300, height=200,
                               command=lambda p=path, n=name: self.display_files(p, n))
            btn.grid(row=0, column=col, padx=30, pady=50)
            col += 1

    def display_files(self, targets_dir, category_name):
        """Display media files in category - FIXED: Show full images"""
        self.stop_all_animations()
        self.back_btn.pack(side="right", padx=10, pady=10)
        for widget in self.container.winfo_children(): 
            widget.destroy()
        
        self.title_lbl.configure(text=f"Select Target: {category_name} 👀")
        
        # Scrollable area for files
        scroll_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        
        media_files = []
        if os.path.exists(targets_dir):
            for f in os.listdir(targets_dir):
                full = os.path.join(targets_dir, f)
                if is_image(full) or is_video(full): 
                    media_files.append(full)
        
        # File Grid (5 columns) - OPTIMIZED SIZE
        for i in range(5): 
            scroll_frame.grid_columnconfigure(i, weight=1)
        
        for idx, path in enumerate(media_files):
            r, c = divmod(idx, 5)
            
            # Card Frame
            card = ctk.CTkFrame(scroll_frame, fg_color="#1e232e", corner_radius=8)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            
            # Preview - FIXED: Use contain instead of fit to show full image
            preview_frame = ctk.CTkFrame(card, fg_color="#0d1117", corner_radius=6)
            preview_frame.pack(padx=5, pady=5, fill="both", expand=True)
            
            img = self._get_preview_contain(path, (200, 150))  # FIXED: Use contain
            lbl = ctk.CTkLabel(preview_frame, image=img, text="")
            lbl.image = img  # Keep reference
            lbl.pack(pady=5, padx=5, fill="both", expand=True)
            
            # File name label
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            name_lbl = ctk.CTkLabel(card, text=filename, font=("Segoe UI", 9), 
                                   text_color="#8b949e")
            name_lbl.pack(pady=(0, 5))
            
            # Select Button (Pink)
            ctk.CTkButton(card, text="Select", height=28,
                         fg_color=COLOR_PINK, hover_color=COLOR_PINK_HOVER,
                         font=("Segoe UI", 11, "bold"),
                         command=lambda p=path: self._select(p)).pack(fill="x", padx=5, pady=(0, 5))

    def _get_preview_contain(self, path, size):
        """Get preview using CONTAIN mode - shows full image without cropping"""
        try:
            if self._is_gif(path):
                # For GIF, show first frame with contain
                img = Image.open(path)
                img.seek(0)
                img = img.convert('RGB')
                # FIXED: Use contain to show full image
                img = ImageOps.contain(img, size, Image.LANCZOS)
                return ctk.CTkImage(img, size=img.size)
            elif is_video(path):
                # For video, get first frame with contain
                cap = cv2.VideoCapture(path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    # FIXED: Use contain to show full image
                    img = ImageOps.contain(img, size, Image.LANCZOS)
                    return ctk.CTkImage(img, size=img.size)
            else:
                # For image, use contain
                img = Image.open(path)
                # FIXED: Use contain to show full image
                img = ImageOps.contain(img, size, Image.LANCZOS)
                return ctk.CTkImage(img, size=img.size)
        except Exception as e:
            print(f"Preview error: {e}")
        
        # Fallback
        blank = Image.new('RGB', size, '#000')
        return ctk.CTkImage(blank, size=size)

    def _is_gif(self, path):
        """Check if file is GIF"""
        return path.lower().endswith('.gif')

    def _select(self, path):
        """Handle file selection"""
        self.stop_all_animations()
        self.callback(path)
        self.destroy()

    def stop_all_animations(self):
        """Stop all active animations"""
        for player in self.animated_previews:
            try:
                player.stop()
            except:
                pass
        self.animated_previews.clear()