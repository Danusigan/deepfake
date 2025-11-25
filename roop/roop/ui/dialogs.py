"""
Dialog windows module - Pink Card Layout
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
        
        self.title("Select Target Category")
        self.geometry("900x600")
        self.configure(fg_color=COLOR_BG)
        self.transient(master)
        self.grab_set()
        
        # Header
        header = ctk.CTkFrame(self, fg_color="#151923", height=50)
        header.pack(fill="x")
        self.title_lbl = ctk.CTkLabel(header, text="Select Target Category (Pipeline Mode)", 
                                     font=("Segoe UI", 18, "bold"), text_color=COLOR_PINK)
        self.title_lbl.pack(side="left", padx=20, pady=10)
        
        self.back_btn = ctk.CTkButton(header, text="⬅ Back", command=self.show_categories,
                                     width=60, fg_color="#333", hover_color="#444")
        
        # Content Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.show_categories()

    def show_categories(self):
        self.back_btn.pack_forget()
        for widget in self.container.winfo_children(): widget.destroy()
        
        self.title_lbl.configure(text="Select Target Category")
        
        # Grid for Categories (3 Columns)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_columnconfigure(2, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Define Icons (Emojis for now to match simplicity)
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
                               width=250, height=180,
                               command=lambda p=path, n=name: self.display_files(p, n))
            btn.grid(row=0, column=col, padx=20, pady=50)
            col += 1

    def display_files(self, targets_dir, category_name):
        self.back_btn.pack(side="right", padx=10, pady=10)
        for widget in self.container.winfo_children(): widget.destroy()
        
        self.title_lbl.configure(text=f"Select Target: {category_name} 💀")
        
        # Scrollable area for files
        scroll_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        
        media_files = []
        if os.path.exists(targets_dir):
            for f in os.listdir(targets_dir):
                full = os.path.join(targets_dir, f)
                if is_image(full) or is_video(full): media_files.append(full)
        
        # File Grid (5 columns)
        for i in range(5): scroll_frame.grid_columnconfigure(i, weight=1)
        
        for idx, path in enumerate(media_files):
            r, c = divmod(idx, 5)
            
            # Card Frame
            card = ctk.CTkFrame(scroll_frame, fg_color="#1e232e", corner_radius=8)
            card.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
            
            # Preview
            img = self._get_preview(path, (140, 90))
            lbl = ctk.CTkLabel(card, image=img, text="")
            lbl.pack(pady=5, padx=5)
            
            # Select Button (Pink)
            ctk.CTkButton(card, text="Select", height=25,
                         fg_color=COLOR_PINK, hover_color=COLOR_PINK_HOVER,
                         command=lambda p=path: self._select(p)).pack(fill="x", padx=5, pady=5)

    def _get_preview(self, path, size):
        try:
            if is_video(path):
                # Simple placeholder for video to keep it fast
                img = Image.new('RGB', size, color='#333') 
            else:
                img = ImageOps.fit(Image.open(path), size, Image.LANCZOS)
            return ctk.CTkImage(img, size=size)
        except:
            return ctk.CTkImage(Image.new('RGB', size, '#000'), size=size)

    def _select(self, path):
        self.callback(path)
        self.destroy()