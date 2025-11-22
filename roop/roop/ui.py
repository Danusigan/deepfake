"""
<<<<<<< Updated upstream
File: roop/ui.py - Complete File with Category-based Target Browser
=======
File: roop/ui.py - Complete File with Custom Target Browser and Deletion
>>>>>>> Stashed changes
"""
from typing import Any, Callable, Tuple, Optional
import cv2
import customtkinter as ctk
import os, sys, tempfile, time
from PIL import Image, ImageOps
from tkinterdnd2 import TkinterDnD, DND_ALL
from tkinter import messagebox # Needed for confirmation dialog

import roop.globals
import roop.metadata
from roop.capturer import get_video_frame, get_video_frame_total
from roop.face_analyser import get_one_face
from roop.face_reference import get_face_reference, set_face_reference, clear_face_reference
from roop.predictor import predict_frame, clear_predictor
from roop.processors.frame.core import get_frame_processors_modules
<<<<<<< Updated upstream
from roop.utilities import is_image, is_video, resolve_relative_path
=======
from roop.utilities import is_image, is_video, resolve_relative_path # resolve_relative_path is kept but not used for TARGETS_DIR now
>>>>>>> Stashed changes
from roop.qr_generator import generate_qr_code

# Globals
ROOT = None
PREVIEW = None
CANVAS = None
RECENT_DIRECTORY_SOURCE = None 
RECENT_DIRECTORY_OUTPUT = None

# Camera - using simple approach
CAM_OBJECT = None
CAM_IS_RUNNING = False
CAM_AFTER_ID = None
CAM_FRAME_DATA = None

# UI Elements
preview_label = preview_slider = source_label = target_label = None
status_label = capture_btn = camera_switch = qr_code_label = None
camera_switch_var = None

<<<<<<< Updated upstream
# ==================== TARGET PATH DEFINITION & CATEGORIES ====================
# The 'targets' folder is in the root directory (one level up from the 'roop' folder).
TARGETS_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'targets'))

# Define categories and their corresponding subfolders
CATEGORIES = {
    "Male 👨": os.path.join(TARGETS_ROOT_DIR, 'Male'),
    "Female 👩": os.path.join(TARGETS_ROOT_DIR, 'Female'),
    "Children 👶": os.path.join(TARGETS_ROOT_DIR, 'Children')
}
# TARGETS_DIR is set dynamically by the browser now, but we'll use TARGETS_ROOT_DIR for the dialog start.
# ==============================================================================
=======
# ==================== CRITICAL FIX APPLIED HERE ====================
# The 'targets' folder is in the root directory (one level up from the 'roop' folder).
# This uses standard Python functions to guarantee the path resolution:
# os.path.dirname(__file__) gets the directory of the current script (roop/).
# os.path.join(..., '..', 'targets') goes up one level and then into 'targets'.
TARGETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'targets'))
# ===================================================================
>>>>>>> Stashed changes


class CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


<<<<<<< Updated upstream
# --- New Class for Custom Target Browser with Category Selection ---

class TargetBrowserDialog(ctk.CTkToplevel):
    def __init__(self, master, categories: dict, callback):
        super().__init__(master)
        self.categories = categories
        self.callback = callback
        self.current_category_path = None
        self.title("🎯 Select & Manage Target Media")
        self.geometry("1000x700") 
        self.resizable(True, True)
        self.transient(master) 
        self.grab_set()        
=======
# --- New Class for Custom Target Browser with Delete Option ---

class TargetBrowserDialog(ctk.CTkToplevel):
    def __init__(self, master, targets_dir, callback):
        super().__init__(master)
        self.targets_dir = targets_dir
        self.callback = callback
        self.title("🎯 Select & Manage Target Media")
        self.geometry("1000x700") # Increased size for better view
        self.resizable(True, True)
        self.transient(master) # Keep above main window
        self.grab_set()        # Modal behavior
>>>>>>> Stashed changes
        
        # Style and setup
        self.configure(fg_color="#0B111D")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
<<<<<<< Updated upstream
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="#0B111D")
        self.header_frame.pack(fill="x", pady=15, padx=30)
        self.title_label = ctk.CTkLabel(self.header_frame, text="Select Target Category", font=("Segoe UI", 24, "bold"), text_color="#C6438D")
        self.title_label.pack(side="left")
        
        # Back Button (initially hidden)
        self.back_button = ctk.CTkButton(self.header_frame, text="◀ Back to Categories", command=self.show_categories,
                                        fg_color="#3a3a3a", hover_color="#5a5a5a", font=("Segoe UI", 14, "bold"))
        
        # Frame for the grid (Scrollable)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="#131826", corner_radius=15, 
                                                       label_text_color="#C6438D", label_font=("Segoe UI", 14, "bold"))
        self.scrollable_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.show_categories()
=======
        ctk.CTkLabel(self, text="Select or Delete Target Media (Images & Videos)", font=("Segoe UI", 24, "bold"), text_color="#C6438D").pack(pady=15)

        # Frame for the grid (Scrollable)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="#131826", corner_radius=15, 
                                                       label_text=f"Files in: {os.path.basename(targets_dir)} and subdirectories", 
                                                       label_text_color="#C6438D", label_font=("Segoe UI", 14, "bold"))
        self.scrollable_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.display_files()
>>>>>>> Stashed changes

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

<<<<<<< Updated upstream
    def show_categories(self):
        self.current_category_path = None
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.title_label.configure(text="Select Target Category")
        self.scrollable_frame.configure(label_text=f"Root Directory: {os.path.basename(TARGETS_ROOT_DIR)}")
        self.back_button.pack_forget()

        # Configure grid for category buttons
        NUM_COLUMNS = 3
        for i in range(NUM_COLUMNS):
            self.scrollable_frame.columnconfigure(i, weight=1)
        
        row = 0
        for index, (category_name, category_path) in enumerate(self.categories.items()):
            col = index % NUM_COLUMNS
            
            category_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#131826", corner_radius=15, height=200, cursor="hand2",
                                          border_width=3, border_color="#C6438D")
            category_frame.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")
            
            category_frame.grid_propagate(False)
            
            # Button to select category
            btn = ctk.CTkButton(category_frame, text=category_name, 
                                command=lambda path=category_path, name=category_name: self.display_files(path, name),
                                fg_color="#C6438D", hover_color="#A52A6D", text_color="black",
                                font=("Segoe UI", 20, "bold"), width=200, height=150)
            btn.place(relx=0.5, rely=0.5, anchor="center")
            
            if col == NUM_COLUMNS - 1:
                row += 1

        if not self.categories:
             ctk.CTkLabel(self.scrollable_frame, text="No categories defined.", text_color="red").pack(pady=50)


    def display_files(self, targets_dir, category_name):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        self.current_category_path = targets_dir
        self.title_label.configure(text=f"Select Target: {category_name}")
        self.scrollable_frame.configure(label_text=f"Files in: {os.path.basename(targets_dir)}")
        self.back_button.pack(side="right")
        
        media_files = []
        try:
            # os.walk is necessary to include subdirectories within the category (e.g., Male/Subfolder)
            for root, _, files in os.walk(targets_dir):
=======
    def display_files(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get all media files (including subdirectories for better browsing)
        media_files = []
        # Use os.walk to include subdirectories, as requested
        try:
            for root, _, files in os.walk(self.targets_dir):
>>>>>>> Stashed changes
                for file in files:
                    full_path = os.path.join(root, file)
                    if is_image(full_path) or is_video(full_path):
                        media_files.append(full_path)
        except Exception as e:
<<<<<<< Updated upstream
            ctk.CTkLabel(self.scrollable_frame, text=f"Error accessing directory: {targets_dir}\n{e}", text_color="red").pack(pady=50)
            return

        if not media_files:
            ctk.CTkLabel(self.scrollable_frame, text=f"No media files found in the '{category_name}' directory.", text_color="gray").pack(pady=50)
            return

        # Configure grid for file icons
        NUM_COLUMNS = 5 
=======
            ctk.CTkLabel(self.scrollable_frame, text=f"Error accessing directory: {self.targets_dir}\n{e}", text_color="red").pack(pady=50)
            return

        if not media_files:
            ctk.CTkLabel(self.scrollable_frame, text="No media files found in the 'targets' directory.", text_color="gray").pack(pady=50)
            return

        # Configure grid for large icons
        NUM_COLUMNS = 5 # Changed to 5 for better fit in 1000px width
>>>>>>> Stashed changes
        for i in range(NUM_COLUMNS):
            self.scrollable_frame.columnconfigure(i, weight=1)
        
        # Display files
        for index, path in enumerate(media_files):
            row = index // NUM_COLUMNS
            col = index % NUM_COLUMNS
            
            # Create a clickable item frame
            item_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="#0B111D", corner_radius=10, border_width=2, border_color="#3a3a3a")
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Use appropriate rendering function
            if is_image(path):
                preview_image = self._render_preview(path, is_video=False)
            elif is_video(path):
                preview_image = self._render_preview(path, is_video=True)
            else:
                 continue

            # Image Label
            img_label = ctk.CTkLabel(item_frame, image=preview_image, text="", compound="top", cursor="hand2")
            img_label.image = preview_image # Keep reference
            img_label.pack(padx=10, pady=(10, 5))
            
<<<<<<< Updated upstream
            # Filename Label (show path relative to the category folder)
            filename = os.path.relpath(path, targets_dir)
=======
            # Filename Label
            filename = os.path.relpath(path, self.targets_dir)
>>>>>>> Stashed changes
            display_name = filename if len(filename) < 25 else filename[:22] + '...'
            
            ctk.CTkLabel(item_frame, text=display_name, font=("Segoe UI", 11), text_color="gray80").pack(padx=10, pady=(0, 5))
            
            # Control Frame (Select/Delete)
            control_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            control_frame.pack(fill="x", padx=10, pady=(0, 10))

<<<<<<< Updated upstream
            # Select Button
=======
            # Select Button (uses the same action as clicking the image)
>>>>>>> Stashed changes
            select_btn = ctk.CTkButton(control_frame, text="Select", command=lambda p=path: self.on_select(p),
                                      fg_color="#C6438D", hover_color="#A52A6D", font=("Segoe UI", 11, "bold"), width=80)
            select_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

<<<<<<< Updated upstream
            # Delete Button 
=======
            # Delete Button (New Feature)
>>>>>>> Stashed changes
            delete_btn = ctk.CTkButton(control_frame, text="🗑️", command=lambda p=path: self.on_delete(p),
                                       fg_color="#CC0000", hover_color="#990000", width=30)
            delete_btn.pack(side="right")
            
            # Bind events to image/frame for selection
            img_label.bind("<Button-1>", lambda e, p=path: self.on_select(p))


    def _render_preview(self, path: str, is_video: bool, size: Tuple[int, int] = (160, 100)) -> ctk.CTkImage:
        try:
            if is_video:
                cap = cv2.VideoCapture(path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    # Draw a black background and a play icon overlay on the video frame
                    temp_frame = frame.copy()
                    cv2.rectangle(temp_frame, (0, 0), (temp_frame.shape[1], temp_frame.shape[0]), (0, 0, 0), -1) 
                    h, w, _ = temp_frame.shape
                    p1 = (w // 2 - 20, h // 2 - 20)
                    p2 = (w // 2 - 20, h // 2 + 20)
                    p3 = (w // 2 + 20, h // 2)
                    cv2.fillConvexPoly(temp_frame, (p1, p2, p3), (0, 168, 168))
                    img = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
                else:
                    img = Image.new('RGB', size, color = 'gray20') # Use a neutral color for missing preview
            else:
                img = Image.open(path)
            
            img_fit = ImageOps.fit(img, size, Image.LANCZOS)
            return ctk.CTkImage(img_fit, size=size)
        except Exception as e:
            print(f"Error rendering preview for {path}: {e}")
            img = Image.new('RGB', size, color = 'red')
            return ctk.CTkImage(img, size=size)


    def on_select(self, path):
        # Callback to the main UI handler
        self.callback(path)
        self.on_close()

    def on_delete(self, path):
        # Confirmation dialog before deleting
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete:\n{os.path.basename(path)}?"):
            try:
                os.remove(path)
                # If the deleted file was the currently selected target, clear the target field
                if roop.globals.target_path == path:
                    roop.globals.target_path = None
                    target_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n🎬\n\nImage or Video")
                    update_status(f"Target removed and deleted.")

<<<<<<< Updated upstream
                # Refresh the view immediately, checking which view we are on
                if self.current_category_path:
                    category_name = [k for k, v in self.categories.items() if v == self.current_category_path][0]
                    self.display_files(self.current_category_path, category_name)
                else:
                    self.show_categories()
=======
                # Refresh the view immediately
                self.display_files()
>>>>>>> Stashed changes
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file:\n{e}")

    def on_close(self):
        self.grab_release()
        self.destroy()

# --- End of TargetBrowserDialog Class ---


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, PREVIEW
    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)
    ROOT.withdraw()
    ROOT.after(50, lambda: (ROOT.deiconify(), ROOT.lift(), ROOT.focus_force(),
                             ROOT.attributes('-topmost', True)))
    ROOT.after(300, lambda: ROOT.attributes('-topmost', False))
    update_status("Ready. Toggle camera ON or drag & drop image.")
    return ROOT


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label, capture_btn, camera_switch, qr_code_label
    global CANVAS, camera_switch_var

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('dark')
    try: ctk.set_default_color_theme(resolve_relative_path('ui.json'))
    except: ctk.set_default_color_theme("blue")

    root = CTk()
    root.minsize(1100, 750)
    root.title(f'{roop.metadata.name} {roop.metadata.version}')
    root.protocol('WM_DELETE_WINDOW', lambda: (destroy_camera(), destroy()))

    # Scrollable canvas
    CANVAS = ctk.CTkCanvas(root, highlightthickness=0, bg='#0B111D')
    scrollbar = ctk.CTkScrollbar(root, orientation="vertical", command=CANVAS.yview)
    main_frame = ctk.CTkFrame(CANVAS, fg_color="#0B111D")
    
    cid = CANVAS.create_window((0, 0), window=main_frame, anchor="nw")
    main_frame.bind("<Configure>", lambda e: CANVAS.configure(scrollregion=CANVAS.bbox("all")))
    CANVAS.bind('<Configure>', lambda e: CANVAS.itemconfig(cid, width=e.width))
    CANVAS.configure(yscrollcommand=scrollbar.set)
    CANVAS.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Global scroll
    def scroll(e): CANVAS.yview_scroll(int(-1*(e.delta/120)), "units")
    root.bind_all("<MouseWheel>", scroll)
    root.bind_all("<Button-4>", lambda e: CANVAS.yview_scroll(-1, "units"))
    root.bind_all("<Button-5>", lambda e: CANVAS.yview_scroll(1, "units"))

    # Header
    header = ctk.CTkFrame(main_frame, fg_color="#0B111D", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(header, text=f"🎭 {roop.metadata.name}", font=("Segoe UI", 30, "bold"),
                 text_color="#00A8A8").pack(pady=20)

    # Content
    content = ctk.CTkFrame(main_frame, fg_color="#0B111D")
    content.pack(fill="both", expand=True, padx=30, pady=20)

    # Cards container - SAME WIDTH using uniform
    cards = ctk.CTkFrame(content, fg_color="transparent")
    cards.pack(fill="x", pady=(0, 20))
    cards.grid_columnconfigure(0, weight=1, uniform="cards")
    cards.grid_columnconfigure(1, weight=1, uniform="cards")

    # ============ SOURCE CARD ============
    src_card = ctk.CTkFrame(cards, fg_color="#131826", corner_radius=20, border_width=2, border_color="#00A8A8")
    src_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    # Header with toggle
    src_header = ctk.CTkFrame(src_card, fg_color="transparent")
    src_header.pack(fill="x", padx=20, pady=(20, 15))
    
    ctk.CTkLabel(src_header, text="👤 Source Face", font=("Segoe UI", 18, "bold"),
                 text_color="#00A8A8").pack(side="left")
    
    # Camera toggle (right side)
    cam_frame = ctk.CTkFrame(src_header, fg_color="transparent")
    cam_frame.pack(side="right")
    ctk.CTkLabel(cam_frame, text="📷", font=("Segoe UI", 14)).pack(side="left", padx=(0, 8))
    camera_switch_var = ctk.BooleanVar(value=False)
    camera_switch = ctk.CTkSwitch(cam_frame, text="", variable=camera_switch_var,
                                   command=handle_camera_toggle, width=45,
                                   progress_color="#00A8A8", button_color="#ffffff",
                                   fg_color="#3a3a3a")
    camera_switch.pack(side="left")
    
    # Source display
    source_label = ctk.CTkLabel(src_card, text="Drag & Drop Image\nor Click to Select\n\n📸\n\nOr toggle camera ON",
                                 fg_color="#0B111D", corner_radius=15, cursor="hand2",
                                 font=("Segoe UI", 12), text_color="gray60", height=200)
    source_label.pack(padx=20, pady=(0, 15), fill="both", expand=True)
    source_label.drop_target_register(DND_ALL)
    source_label.dnd_bind('<<Drop>>', lambda e: select_source_path(e.data))
    source_label.bind('<Button-1>', lambda e: select_source_path())

    # Capture button
    capture_btn = ctk.CTkButton(src_card, text='📸 Capture Face', command=do_capture,
                                 fg_color="#00A8A8", hover_color="#008585", text_color="black",
                                 height=45, corner_radius=12, font=("Segoe UI", 13, "bold"),
                                 state='disabled')
    capture_btn.pack(padx=20, pady=(0, 20), fill="x")

    # ============ TARGET CARD ============
    tgt_card = ctk.CTkFrame(cards, fg_color="#131826", corner_radius=20, border_width=2, border_color="#C6438D")
    tgt_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    # Header
    tgt_header = ctk.CTkFrame(tgt_card, fg_color="transparent")
    tgt_header.pack(fill="x", padx=20, pady=(20, 15))
    ctk.CTkLabel(tgt_header, text="🎯 Target Media", font=("Segoe UI", 18, "bold"),
                 text_color="#C6438D").pack(side="left")
    
    # Target display
    target_label = ctk.CTkLabel(tgt_card, text="Drag & Drop\nor Click to Select\n\n🎬\n\nImage or Video",
                                 fg_color="#0B111D", corner_radius=15, cursor="hand2",
                                 font=("Segoe UI", 12), text_color="gray60", height=200)
    target_label.pack(padx=20, pady=(0, 15), fill="both", expand=True)
    target_label.drop_target_register(DND_ALL)
    target_label.dnd_bind('<<Drop>>', lambda e: select_target_path(e.data))
    target_label.bind('<Button-1>', lambda e: select_target_path())
    
    # Browse button
    ctk.CTkButton(tgt_card, text='📁 Browse Files', command=select_target_path,
                  fg_color="#C6438D", hover_color="#A52A6D", height=45,
                  corner_radius=12, font=("Segoe UI", 13, "bold")).pack(padx=20, pady=(0, 20), fill="x")

    # Status
    status_frame = ctk.CTkFrame(content, fg_color="#131826", corner_radius=12, height=55)
    status_frame.pack(fill="x", pady=(0, 20))
    status_frame.pack_propagate(False)
    ctk.CTkLabel(status_frame, text="📊", font=("Segoe UI", 14)).pack(side="left", padx=(15, 5), pady=12)
    status_label = ctk.CTkLabel(status_frame, text="Ready", font=("Segoe UI", 13), text_color="#7CFC00")
    status_label.pack(side="left", padx=5, pady=12)

    # Output section
    out_frame = ctk.CTkFrame(content, fg_color="#131826", corner_radius=15)
    out_frame.pack(fill="x", pady=(0, 20))
    ctk.CTkLabel(out_frame, text="✨ Output & QR Code", font=("Segoe UI", 16, "bold"),
                 text_color="#6AA84F").pack(pady=(15, 10))
    
    out_grid = ctk.CTkFrame(out_frame, fg_color="transparent")
    out_grid.pack(padx=20, pady=(0, 20), fill="x")
    out_grid.grid_columnconfigure(0, weight=1, uniform="out")
    out_grid.grid_columnconfigure(1, weight=1, uniform="out")
    
    output_label = ctk.CTkLabel(out_grid, text="Output preview\nwill appear here", fg_color="#0B111D",
                                 corner_radius=12, height=220, font=("Segoe UI", 12), text_color="gray60")
    output_label.grid(row=0, column=0, padx=10, sticky="nsew")
    root._output_label = output_label
    
    qr_code_label = ctk.CTkLabel(out_grid, text="QR Code\nfor sharing", fg_color="#0B111D",
                                  corner_radius=12, height=220, font=("Segoe UI", 12), text_color="gray60")
    qr_code_label.grid(row=0, column=1, padx=10, sticky="nsew")

    # ============ SETTINGS PANEL (Like Original) ============
    settings_frame = ctk.CTkFrame(content, fg_color="#131826", corner_radius=15)
    settings_frame.pack(fill="x", pady=(0, 20))

    ctk.CTkLabel(settings_frame, text="⚙️ Advanced Settings", font=("Segoe UI", 16, "bold"),
                 text_color="#00A8A8").pack(pady=(15, 10), padx=20, anchor="w")

    settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
    settings_grid.pack(fill="x", padx=20, pady=(0, 15))
    settings_grid.grid_columnconfigure(0, weight=1, uniform="sett")
    settings_grid.grid_columnconfigure(1, weight=1, uniform="sett")

    # General Settings (Left)
    general_section = ctk.CTkFrame(settings_grid, fg_color="#0B111D", corner_radius=10)
    general_section.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(general_section, text="🎬 Video Options", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    keep_fps_value = ctk.BooleanVar(value=roop.globals.keep_fps)
    ctk.CTkSwitch(general_section, text='Keep Original FPS', variable=keep_fps_value, cursor='hand2',
                  command=lambda: setattr(roop.globals, 'keep_fps', keep_fps_value.get()),
                  progress_color="#00A8A8").pack(pady=5, padx=15, anchor="w")

    skip_audio_value = ctk.BooleanVar(value=roop.globals.skip_audio)
    ctk.CTkSwitch(general_section, text='Mute Audio', variable=skip_audio_value, cursor='hand2',
                  command=lambda: setattr(roop.globals, 'skip_audio', skip_audio_value.get()),
                  progress_color="#00A8A8").pack(pady=5, padx=15, anchor="w")

    keep_frames_value = ctk.BooleanVar(value=roop.globals.keep_frames)
    ctk.CTkSwitch(general_section, text='Keep Temp Frames', variable=keep_frames_value, cursor='hand2',
                  command=lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()),
                  progress_color="#00A8A8").pack(pady=(5, 15), padx=15, anchor="w")

    # Face Detection Settings (Right)
    face_section = ctk.CTkFrame(settings_grid, fg_color="#0B111D", corner_radius=10)
    face_section.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(face_section, text="👥 Face Detection", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    many_faces_value = ctk.BooleanVar(value=roop.globals.many_faces)
    ctk.CTkSwitch(face_section, text='Process All Faces', variable=many_faces_value, cursor='hand2',
                  command=lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()),
                  progress_color="#C6438D").pack(pady=5, padx=15, anchor="w")

    ref_frame = ctk.CTkFrame(face_section, fg_color="transparent")
    ref_frame.pack(pady=5, padx=15, fill="x")
    ctk.CTkLabel(ref_frame, text="Face Index:", font=("Segoe UI", 11)).pack(side="left")
    reference_entry = ctk.CTkEntry(ref_frame, width=60, placeholder_text="0")
    reference_entry.pack(side="left", padx=(10, 0))
    reference_entry.insert(0, "0")

    ctk.CTkLabel(face_section, text="Similar Face Distance: 0.85", font=("Segoe UI", 10),
                 text_color="gray60").pack(pady=(5, 15), padx=15, anchor="w")

    # Performance Settings (Left Bottom)
    perf_section = ctk.CTkFrame(settings_grid, fg_color="#0B111D", corner_radius=10)
    perf_section.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(perf_section, text="⚡ Performance", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    thread_frame = ctk.CTkFrame(perf_section, fg_color="transparent")
    thread_frame.pack(pady=5, padx=15, fill="x")
    ctk.CTkLabel(thread_frame, text="Execution Threads:", font=("Segoe UI", 11)).pack(anchor="w")
    threads_slider = ctk.CTkSlider(thread_frame, from_=1, to=16, number_of_steps=15, progress_color="#00A8A8")
    threads_slider.set(roop.globals.execution_threads if hasattr(roop.globals, 'execution_threads') else 8)
    threads_slider.pack(fill="x", pady=5)

    mem_frame = ctk.CTkFrame(perf_section, fg_color="transparent")
    mem_frame.pack(pady=5, padx=15, fill="x")
    ctk.CTkLabel(mem_frame, text="Max Memory (GB):", font=("Segoe UI", 11)).pack(anchor="w")
    memory_slider = ctk.CTkSlider(mem_frame, from_=1, to=64, number_of_steps=63, progress_color="#00A8A8")
    memory_slider.set(roop.globals.max_memory if roop.globals.max_memory else 8)
    memory_slider.pack(fill="x", pady=(5, 15))

    # Output Settings (Right Bottom)
    output_section = ctk.CTkFrame(settings_grid, fg_color="#0B111D", corner_radius=10)
    output_section.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(output_section, text="💾 Output Options", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    provider_frame = ctk.CTkFrame(output_section, fg_color="transparent")
    provider_frame.pack(pady=5, padx=15, fill="x")
    ctk.CTkLabel(provider_frame, text="Execution Provider:", font=("Segoe UI", 11)).pack(anchor="w")
    provider_combo = ctk.CTkComboBox(provider_frame, values=["cpu", "cuda", "coreml", "openvino"],
                                     button_color="#00A8A8", button_hover_color="#008585")
    provider_combo.set("cpu")
    provider_combo.pack(fill="x", pady=5)

    quality_frame = ctk.CTkFrame(output_section, fg_color="transparent")
    quality_frame.pack(pady=5, padx=15, fill="x")
    ctk.CTkLabel(quality_frame, text="Output Quality:", font=("Segoe UI", 11)).pack(anchor="w")
    quality_slider = ctk.CTkSlider(quality_frame, from_=0, to=100, number_of_steps=100, progress_color="#C6438D")
    quality_slider.set(roop.globals.output_video_quality if hasattr(roop.globals, 'output_video_quality') else 35)
    quality_slider.pack(fill="x", pady=(5, 15))

    # Start button
    ctk.CTkButton(content, text='🚀 Start Processing', command=lambda: select_output_path(start),
                  fg_color="#6AA84F", hover_color="#588E3E", text_color="black",
                  height=50, width=250, corner_radius=12, font=("Segoe UI", 15, "bold")).pack(pady=25)

    ctk.CTkLabel(content, text=f"v{roop.metadata.version} | Powered by AI", 
                 font=("Segoe UI", 10), text_color="gray50").pack(pady=(5, 20))

    return root


def create_preview(parent):
    global preview_label, preview_slider
    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.protocol('WM_DELETE_WINDOW', toggle_preview)
    preview.resizable(False, False)
    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)
    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda v: update_preview(v))
    preview.bind('<Up>', lambda e: update_face_reference(1))
    preview.bind('<Down>', lambda e: update_face_reference(-1))
    return preview


# ==================== CAMERA FUNCTIONS ====================

def stop_camera_feed():
    """Stop camera feed loop only"""
    global CAM_IS_RUNNING, CAM_AFTER_ID
    CAM_IS_RUNNING = False
    if CAM_AFTER_ID is not None:
        try:
            ROOT.after_cancel(CAM_AFTER_ID)
        except:
            pass
        CAM_AFTER_ID = None


def release_camera():
    """Release camera hardware"""
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
    """Full cleanup"""
    release_camera()
    try:
        cv2.destroyAllWindows()
    except:
        pass


def open_camera():
    """Open camera fresh"""
    global CAM_OBJECT
    
    # Release if exists
    release_camera()
    time.sleep(0.3)
    
    print("[DEBUG] Creating VideoCapture with DirectShow...")
    # Open with DirectShow (best for Windows)
    CAM_OBJECT = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if CAM_OBJECT is None or not CAM_OBJECT.isOpened():
        print("[DEBUG] DirectShow failed, trying default...")
        # Fallback to default
        CAM_OBJECT = cv2.VideoCapture(0)
    
    if CAM_OBJECT is not None and CAM_OBJECT.isOpened():
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        CAM_OBJECT.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Test read
        ret, frame = CAM_OBJECT.read()
        print(f"[DEBUG] Test read: ret={ret}, frame shape={frame.shape if frame is not None else None}")
        if ret:
            return True
    
    print("[DEBUG] Camera open failed completely")
    release_camera()
    return False


def handle_camera_toggle():
    """Handle camera toggle - simple version"""
    global CAM_IS_RUNNING
    
    if camera_switch_var.get():
        # TURN ON
        update_status("Opening camera...")
        ROOT.update()
        
        print("[DEBUG] Attempting to open camera...")
        if open_camera():
            print("[DEBUG] Camera opened successfully")
            CAM_IS_RUNNING = True
            roop.globals.source_path = None
            capture_btn.configure(state='normal', text='📸 Capture Face', command=do_capture)
            update_status("Camera ON - Capture when ready")
            print("[DEBUG] Starting camera feed...")
            start_camera_feed()
        else:
            print("[DEBUG] Failed to open camera")
            camera_switch_var.set(False)
            capture_btn.configure(state='disabled')
            update_status("Cannot open camera!")
    else:
        # TURN OFF
        print("[DEBUG] Turning camera OFF")
        release_camera()
        capture_btn.configure(state='disabled', text='📸 Capture Face')
        if not roop.globals.source_path:
            source_label.configure(image=None, text="Drag & Drop Image\nor Click to Select\n\n📸\n\nOr toggle camera ON")
        update_status("Camera OFF")


def start_camera_feed():
    """Start the camera feed"""
    global CAM_IS_RUNNING
    print("[DEBUG] start_camera_feed called")
    print(f"[DEBUG] source_label exists: {source_label is not None}")
    CAM_IS_RUNNING = True
    # Call first tick immediately
    ROOT.after(100, camera_feed_tick)


def camera_feed_tick():
    """Single tick of camera feed"""
    global CAM_AFTER_ID, CAM_FRAME_DATA, CAM_IMAGE_REF
    
    # Check if should continue
    if not CAM_IS_RUNNING:
        print("[DEBUG] Feed tick: not running, stopping")
        return
    
    if CAM_OBJECT is None or not CAM_OBJECT.isOpened():
        print("[DEBUG] Feed tick: camera not available")
        # Camera lost - try to recover once
        if open_camera():
            CAM_AFTER_ID = ROOT.after(50, camera_feed_tick)
        else:
            camera_switch_var.set(False)
            capture_btn.configure(state='disabled')
            source_label.configure(image=None, text="Camera lost!\n\nToggle to retry")
            update_status("Camera disconnected")
        return
    
    try:
        ret, frame = CAM_OBJECT.read()
        if ret and frame is not None:
            CAM_FRAME_DATA = frame.copy()
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Create PIL Image
            pil_img = Image.fromarray(rgb)
            # Resize to fit
            pil_img = ImageOps.fit(pil_img, (280, 180), Image.LANCZOS)
            # Create CTkImage and KEEP REFERENCE
            CAM_IMAGE_REF = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(280, 180))
            # Update label
            source_label.configure(image=CAM_IMAGE_REF, text="")
            # Force update
            source_label.update_idletasks()
    except Exception as e:
        print(f"[DEBUG] Feed error: {e}")
    
    # Schedule next tick
    if CAM_IS_RUNNING:
        CAM_AFTER_ID = ROOT.after(40, camera_feed_tick)


def do_capture():
    """Capture current frame"""
    global CAM_FRAME_DATA
    
    if CAM_FRAME_DATA is None:
        update_status("No frame yet - wait a moment")
        return
    
    # Stop feed but KEEP camera open
    stop_camera_feed()
    
    # Save frame
    path = os.path.join(tempfile.gettempdir(), f"roop_src_{int(time.time())}.png")
    try:
        cv2.imwrite(path, CAM_FRAME_DATA)
        roop.globals.source_path = path
        source_label.configure(image=render_image_preview(path, (280, 180)), text="")
        capture_btn.configure(text='🔄 Re-capture', command=do_recapture)
        update_status("Captured! Re-capture or start processing")
    except Exception as e:
        update_status(f"Error: {e}")
        do_recapture()


def do_recapture():
    """Re-capture - just restart feed (camera still open)"""
    global CAM_FRAME_DATA
    
    if not camera_switch_var.get():
        update_status("Turn camera ON first")
        return
    
    CAM_FRAME_DATA = None
    roop.globals.source_path = None
    capture_btn.configure(text='📸 Capture Face', command=do_capture)
    update_status("Camera ready")
    start_camera_feed()


# ==================== FILE FUNCTIONS ====================

def update_status(text: str):
    if status_label:
        status_label.configure(text=text)
    if ROOT:
        ROOT.update_idletasks()


def select_source_path(path: Optional[str] = None):
    global RECENT_DIRECTORY_SOURCE, CAM_IS_RUNNING, CAM_AFTER_ID
    
    # Pause camera
    CAM_IS_RUNNING = False
    if CAM_AFTER_ID:
        try: ROOT.after_cancel(CAM_AFTER_ID)
        except: pass
        CAM_AFTER_ID = None
    
    if PREVIEW: PREVIEW.withdraw()
    
    if not path:
        path = ctk.filedialog.askopenfilename(title='Select source image', initialdir=RECENT_DIRECTORY_SOURCE,
                                               filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp"), ("All", "*.*")])
    
    path = path.strip('{}').strip() if path else None
    
    if path and is_image(path):
        try:
            roop.globals.source_path = path
            RECENT_DIRECTORY_SOURCE = os.path.dirname(path)
            source_label.configure(image=render_image_preview(path, (280, 180)), text="")
            capture_btn.configure(text='📸 Capture Face', command=do_capture)
            update_status(f"Source: {os.path.basename(path)}")
        except Exception as e:
            update_status(f"Error: {e}")
    elif not path and camera_switch_var.get() and CAM_OBJECT and CAM_OBJECT.isOpened():
        # Resume camera if dialog cancelled
        CAM_IS_RUNNING = True
        start_camera_feed()


def select_target_path(path: Optional[str] = None):
<<<<<<< Updated upstream
    # This function is now the entry point for the category browser
=======
    global TARGETS_DIR
>>>>>>> Stashed changes
    if PREVIEW: PREVIEW.withdraw()
    clear_face_reference()
    
    if not path:
<<<<<<< Updated upstream
        # Check if the root targets directory exists
        if not os.path.isdir(TARGETS_ROOT_DIR):
            update_status(f"Error: Root target directory '{TARGETS_ROOT_DIR}' not found. Create it.")
            return

        # Launch the custom browser dialog showing categories
        TargetBrowserDialog(ROOT, CATEGORIES, handle_target_selection)
=======
        # Check if targets directory exists
        if not os.path.isdir(TARGETS_DIR):
            # Display the absolute path it's trying to find for better debugging
            update_status(f"Error: Target directory '{TARGETS_DIR}' not found. Check path.")
            return

        # Launch the custom browser dialog
        TargetBrowserDialog(ROOT, TARGETS_DIR, handle_target_selection)
>>>>>>> Stashed changes
        
    else:
        # This handles drag & drop operations directly (path is provided)
        handle_target_selection(path)


def handle_target_selection(path):
    # This function processes the path selected from the custom dialog or drag/drop
    path = path.strip('{}').strip() if path else None
    
    if path and is_image(path):
        roop.globals.target_path = path
        target_label.configure(image=render_image_preview(path, (280, 180)), text="")
        update_status(f"Target: {os.path.basename(path)}")
    elif path and is_video(path):
        roop.globals.target_path = path
        target_label.configure(image=render_video_preview(path, (280, 180)), text="")
        update_status(f"Target: {os.path.basename(path)}")


def select_output_path(start: Callable[[], None]):
    global RECENT_DIRECTORY_OUTPUT
    
    if not roop.globals.target_path:
        update_status("Select target first!")
        return
    
    if not roop.globals.source_path:
        update_status("Select or capture source face first!")
        return
    
    ext = '.png' if is_image(roop.globals.target_path) else '.mp4' if is_video(roop.globals.target_path) else None
    if not ext: return
    
    path = ctk.filedialog.asksaveasfilename(title='Save output', defaultextension=ext,
                                             initialfile=f'output{ext}', initialdir=RECENT_DIRECTORY_OUTPUT)
    if path:
        roop.globals.output_path = path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(path)
        start()
        try:
            if os.path.exists(path):
                prev = render_image_preview(path, (350, 200)) if is_image(path) else render_video_preview(path, (350, 200))
                ROOT._output_label.configure(image=prev, text="")
                generate_qr_for_output(path)
        except: pass


def generate_qr_for_output(path: str):
    try:
        qr_code_label.configure(image=generate_qr_code(f"https://share.roop/{os.path.basename(path)}", (180, 180)), text="")
    except:
        qr_code_label.configure(text="QR Failed")


def render_image_preview(path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    img = ImageOps.fit(Image.open(path), size, Image.LANCZOS)
    return ctk.CTkImage(img, size=size)


def render_video_preview(path: str, size: Tuple[int, int], frame_num: int = 0) -> Optional[ctk.CTkImage]:
    cap = cv2.VideoCapture(path)
    if frame_num: cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    cap.release()
    if ret:
        img = ImageOps.fit(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), size, Image.LANCZOS)
        return ctk.CTkImage(img, size=size)
    return None


# ==================== PREVIEW FUNCTIONS ====================

def toggle_preview():
    if PREVIEW.state() == 'normal':
        PREVIEW.unbind('<Right>')
        PREVIEW.unbind('<Left>')
        PREVIEW.withdraw()
        clear_predictor()
    elif roop.globals.source_path and roop.globals.target_path:
        init_preview()
        update_preview(roop.globals.reference_frame_number)
        PREVIEW.deiconify()


def init_preview():
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
    if roop.globals.source_path and roop.globals.target_path:
        temp = get_video_frame(roop.globals.target_path, frame_num)
        if predict_frame(temp): sys.exit()
        src_face = get_one_face(cv2.imread(roop.globals.source_path))
        if not get_face_reference():
            ref = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            set_face_reference(get_one_face(ref, roop.globals.reference_face_position))
        for proc in get_frame_processors_modules(roop.globals.frame_processors):
            temp = proc.process_frame(src_face, get_face_reference(), temp)
        img = ImageOps.contain(Image.fromarray(cv2.cvtColor(temp, cv2.COLOR_BGR2RGB)), (1200, 700), Image.LANCZOS)
        preview_label.configure(image=ctk.CTkImage(img, size=img.size))


def update_face_reference(steps: int):
    clear_face_reference()
    roop.globals.reference_face_position += steps
    roop.globals.reference_frame_number = int(preview_slider.get())
    update_preview(roop.globals.reference_frame_number)


def update_frame(steps: int):
    preview_slider.set(preview_slider.get() + steps)
    update_preview(preview_slider.get())