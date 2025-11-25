"""
Main window module - Fixed Capture Button
"""

from typing import Callable
import customtkinter as ctk
try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
import roop.globals
import roop.metadata

# Import other modules
from . import camera, file_handlers, preview, pipeline

# Global references
ROOT = None
_target_label = None
_source_label = None
_pipeline_switch_var = None
_camera_switch_var = None

# --- COLORS ---
COLOR_BG = "#0b101a"
COLOR_CARD_BG = "#0f1520"
COLOR_CYAN = "#00E5FF"
COLOR_CYAN_BTN = "#00bcd4"
COLOR_PINK = "#E91E63"
COLOR_PINK_BTN = "#d81b60"
COLOR_GREEN = "#4CAF50"
COLOR_GREEN_HOVER = "#388E3C"

if DND_AVAILABLE:
    class CTk(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class CTk(ctk.CTk):
        pass


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT
    ROOT = create_root(start, destroy)
    try:
        PREVIEW = preview.create_preview(ROOT)
    except Exception as e:
        print(f"Preview init failed: {e}")
    ROOT.withdraw()
    ROOT.after(50, lambda: (ROOT.deiconify(), ROOT.lift(), ROOT.focus_force()))
    return ROOT


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, _target_label, _source_label, _pipeline_switch_var, _camera_switch_var
    
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    
    ROOT = CTk()
    ROOT.title(f'{roop.metadata.name} {roop.metadata.version}')
    ROOT.geometry('1100x750')
    ROOT.configure(fg_color=COLOR_BG)
    
    ROOT.grid_columnconfigure(0, weight=1)
    ROOT.grid_rowconfigure(0, weight=0)
    ROOT.grid_rowconfigure(1, weight=1)
    ROOT.grid_rowconfigure(2, weight=0)
    
    # ===== 1. HEADER =====
    header_frame = ctk.CTkFrame(ROOT, fg_color="transparent", height=40)
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
    
    status_label = ctk.CTkLabel(header_frame, text="Ready", 
                               font=("Consolas", 12), text_color="#00FF00", anchor="w")
    status_label.pack(side="left")
    
    # ===== 2. MAIN CONTENT =====
    content_frame = ctk.CTkFrame(ROOT, fg_color="transparent")
    content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=1)
    content_frame.grid_rowconfigure(0, weight=1)

    # --- LEFT: SOURCE (CYAN) ---
    source_frame = ctk.CTkFrame(content_frame, fg_color=COLOR_CARD_BG, 
                               border_width=2, border_color=COLOR_CYAN, corner_radius=15)
    source_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    source_frame.grid_columnconfigure(0, weight=1)
    source_frame.grid_rowconfigure(1, weight=1)
    
    src_header = ctk.CTkFrame(source_frame, fg_color="transparent", height=30)
    src_header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
    ctk.CTkLabel(src_header, text="👤 Source Face", font=("Segoe UI", 14, "bold"), text_color=COLOR_CYAN).pack(side="left")
    
    _camera_switch_var = ctk.BooleanVar(value=False)
    cam_switch = ctk.CTkSwitch(src_header, text="📷", variable=_camera_switch_var, 
                              command=camera.handle_camera_toggle,
                              progress_color=COLOR_CYAN, button_color="#ffffff",
                              button_hover_color="#eeeeee", width=40)
    cam_switch.pack(side="right")
    
    _source_label = ctk.CTkLabel(source_frame, text="Drag & Drop Image\nor Click to Select\n\nOr toggle camera ON",
                                fg_color="#000000", corner_radius=10, text_color="#555555")
    _source_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
    
    # FIX: Added command and initial state
    capture_btn = ctk.CTkButton(source_frame, text="📸 Capture Face", height=45,
                               command=lambda: camera.do_capture(),
                               state="disabled",
                               fg_color=COLOR_CYAN_BTN, hover_color=COLOR_CYAN,
                               text_color="#000000", font=("Segoe UI", 13, "bold"))
    capture_btn.grid(row=2, column=0, sticky="ew", padx=15, pady=15)


    # --- RIGHT: TARGET (PINK) ---
    target_frame = ctk.CTkFrame(content_frame, fg_color=COLOR_CARD_BG, 
                               border_width=2, border_color=COLOR_PINK, corner_radius=15)
    target_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    target_frame.grid_columnconfigure(0, weight=1)
    target_frame.grid_rowconfigure(1, weight=1)
    
    tgt_header = ctk.CTkFrame(target_frame, fg_color="transparent", height=30)
    tgt_header.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
    ctk.CTkLabel(tgt_header, text="🎯 Target Media", font=("Segoe UI", 14, "bold"), text_color=COLOR_PINK).pack(side="left")

    _target_label = ctk.CTkLabel(target_frame, text="Drag & Drop\nor Click to Select",
                                fg_color="#000000", corner_radius=10, text_color="#555555")
    _target_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
    
    browse_btn = ctk.CTkButton(target_frame, text="📁 Browse Files", height=45,
                               command=lambda: file_handlers.select_target_path(),
                               fg_color=COLOR_PINK_BTN, hover_color=COLOR_PINK,
                               text_color="#ffffff", font=("Segoe UI", 13, "bold"))
    browse_btn.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
    
    
    # ===== 3. FOOTER =====
    footer_frame = ctk.CTkFrame(ROOT, fg_color="transparent")
    footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
    footer_frame.grid_columnconfigure(0, weight=1)
    
    ctk.CTkLabel(footer_frame, text="✨ Output & QR Code", font=("Segoe UI", 12, "bold"), text_color="#8bc34a").pack(anchor="w", pady=(0,5))
    
    output_container = ctk.CTkFrame(footer_frame, fg_color=COLOR_CARD_BG, corner_radius=10)
    output_container.pack(fill="x", expand=True)
    output_container.grid_columnconfigure(0, weight=1)
    output_container.grid_columnconfigure(1, weight=1)
    
    output_label = ctk.CTkLabel(output_container, text="Output preview\nwill appear here", 
                               fg_color="#080808", corner_radius=8, height=140, text_color="#444")
    output_label.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    qr_code_label = ctk.CTkLabel(output_container, text="QR Code\nfor sharing", 
                                fg_color="#080808", corner_radius=8, height=140, text_color="#444")
    qr_code_label.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
    
    # ACTION BAR
    action_bar = ctk.CTkFrame(footer_frame, fg_color="transparent")
    action_bar.pack(fill="x", pady=20)
    action_bar.grid_columnconfigure(0, weight=1)
    action_bar.grid_columnconfigure(1, weight=0) # Center
    action_bar.grid_columnconfigure(2, weight=1)

    # Options (Left)
    opts_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
    opts_frame.grid(row=0, column=0, sticky="w", padx=10)
    ctk.CTkCheckBox(opts_frame, text="Keep FPS", variable=ctk.BooleanVar(value=True), font=("Segoe UI", 11), width=20, height=20, border_width=2).pack(side="left", padx=5)
    ctk.CTkCheckBox(opts_frame, text="Skip Audio", variable=ctk.BooleanVar(value=False), font=("Segoe UI", 11), width=20, height=20, border_width=2).pack(side="left", padx=5)

    # Start Button (Center)
    start_btn = ctk.CTkButton(action_bar, text="🚀 Start Processing", height=45, width=220,
                             command=lambda: file_handlers.select_output_path(start),
                             fg_color=COLOR_GREEN, hover_color=COLOR_GREEN_HOVER,
                             text_color="#000000", font=("Segoe UI", 14, "bold"), corner_radius=22)
    start_btn.grid(row=0, column=1)

    # Pipeline Toggle (Right)
    _pipeline_switch_var = ctk.BooleanVar(value=roop.globals.PIPELINE_ENABLED)
    pipe_switch = ctk.CTkSwitch(action_bar, text="Pipeline Mode", variable=_pipeline_switch_var, 
                               command=pipeline.handle_pipeline_toggle, 
                               progress_color=COLOR_PINK, font=("Segoe UI", 12, "bold"))
    pipe_switch.grid(row=0, column=2, sticky="e", padx=10)
    
    # Init References
    file_handlers.init_file_handler_references(ROOT, status_label, _target_label, _source_label, output_label, qr_code_label, capture_btn)
    camera.init_camera_references(ROOT, _source_label, capture_btn, _camera_switch_var)
    pipeline.init_pipeline_references(ROOT, capture_btn)
    
    if DND_AVAILABLE:
        setup_drag_drop(_source_label, _target_label)
        
    _source_label.bind('<Button-1>', lambda e: file_handlers.select_source_path())
    _target_label.bind('<Button-1>', lambda e: file_handlers.select_target_path())
    
    return ROOT

def setup_drag_drop(source_label, target_label):
    if not DND_AVAILABLE: return
    source_label.drop_target_register('DND_Files')
    source_label.dnd_bind('<<Drop>>', lambda e: file_handlers.select_source_path(e.data))
    target_label.drop_target_register('DND_Files')
    target_label.dnd_bind('<<Drop>>', lambda e: file_handlers.select_target_path(e.data))

def get_root(): return ROOT
def get_target_label(): return _target_label
def get_pipeline_switch_var(): return _pipeline_switch_var
def get_camera_switch_var(): return _camera_switch_var