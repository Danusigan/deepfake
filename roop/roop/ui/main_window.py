"""
Main window module - Modern AI UI Layout (Fixed Colors)
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
_keep_fps_var = None
_skip_audio_var = None
_keep_frames_var = None
_many_faces_var = None

# --- MODERN AI STUDIO COLOR PALETTE ---
COLOR_BG = "#0b0f19"          # Very dark slate background
COLOR_HEADER_BG = "#111625"   # Slightly lighter header
COLOR_CARD_BG = "#161b22"     # Card background
COLOR_PREVIEW_BG = "#0d1117"  # Recessed background for images
COLOR_BORDER = "#30363d"      # Subtle border color

# Neon Accents & Hover States
COLOR_CYAN = "#00f2ea"        
COLOR_CYAN_HOVER = "#00b8d4"  # <--- Added this

COLOR_PINK = "#ff0055"        
COLOR_PINK_HOVER = "#C2185B"  # <--- Added this

COLOR_GREEN = "#00e676"       
COLOR_GREEN_HOVER = "#00c853" # <--- Added this

COLOR_PURPLE = "#d500f9"      

COLOR_TEXT_PRIMARY = "#f0f6fc"
COLOR_TEXT_SECONDARY = "#8b949e"

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
    global _keep_fps_var, _skip_audio_var, _keep_frames_var, _many_faces_var
    
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    
    ROOT = CTk()
    ROOT.state('zoomed')  # Maximizes window, recommended for Windows laptops
    

    ROOT.title(f'{roop.metadata.name} {roop.metadata.version}')
    ROOT.geometry('1100x850')
    ROOT.configure(fg_color=COLOR_BG)
    ROOT.resizable(True, True)
    
    # === MAIN GRID ===
    ROOT.grid_columnconfigure(0, weight=1)
    # Row weights determine what expands
    ROOT.grid_rowconfigure(0, weight=0)  # Header (Fixed)
    ROOT.grid_rowconfigure(1, weight=1)  # Layer 1: Inputs (Expands)
    ROOT.grid_rowconfigure(2, weight=1)  # Layer 2: Output/QR (Expands)
    ROOT.grid_rowconfigure(3, weight=0)  # Settings (Fixed)
    ROOT.grid_rowconfigure(4, weight=0)  # Button (Fixed)

    # ==========================================================
    # 1. HEADER BAR
    # ==========================================================
    header_frame = ctk.CTkFrame(ROOT, fg_color=COLOR_HEADER_BG, corner_radius=0, height=55)
    header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    header_frame.grid_columnconfigure(1, weight=1) # Spacer

    # Brand / Logo Area
    title_label = ctk.CTkLabel(header_frame, text="🎭 ROOP", font=("Segoe UI", 16, "bold"), 
                               text_color=COLOR_TEXT_PRIMARY)
    title_label.grid(row=0, column=0, padx=20, pady=10)

    # Status (Center)
    status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    status_frame.grid(row=0, column=1)
    status_icon = ctk.CTkLabel(status_frame, text="●", font=("Segoe UI", 14), text_color=COLOR_GREEN)
    status_icon.pack(side="left", padx=(0, 5))
    status_label = ctk.CTkLabel(status_frame, text="System Ready", 
                                font=("Segoe UI", 12), text_color=COLOR_TEXT_SECONDARY)
    status_label.pack(side="left")

    # Pipeline Toggle (Right)
    _pipeline_switch_var = ctk.BooleanVar(value=roop.globals.PIPELINE_ENABLED)
    pipe_switch = ctk.CTkSwitch(
        header_frame, 
        text="Auto mode", 
        variable=_pipeline_switch_var, 
        command=pipeline.handle_pipeline_toggle, 
        progress_color=COLOR_PINK,
        font=("Segoe UI", 11, "bold"),
        text_color=COLOR_TEXT_PRIMARY,
        fg_color="#333"
    )
    pipe_switch.grid(row=0, column=2, padx=20)

    # ==========================================================
    # 2. LAYER ONE: INPUTS (Source & Target)
    # ==========================================================
    # Added pady at bottom to create the "Gap" between layers
    layer_one = ctk.CTkFrame(ROOT, fg_color="transparent")
    layer_one.grid(row=1, column=0, sticky="nsew", padx=20, pady=(20, 10))
    layer_one.grid_columnconfigure(0, weight=1)
    layer_one.grid_columnconfigure(1, weight=1)
    layer_one.grid_rowconfigure(0, weight=1)

    # Source Card
    source_card = create_modern_card(layer_one, "SOURCE FACE", COLOR_CYAN, True)
    source_card['frame'].grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    _source_label = source_card['label']
    _camera_switch_var = source_card['camera_var']
    capture_btn = source_card['action_btn']

    # Target Card
    target_card = create_modern_card(layer_one, "TARGET MEDIA", COLOR_PINK, False)
    target_card['frame'].grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    _target_label = target_card['label']

    # ==========================================================
    # 3. LAYER TWO: OUTPUTS (Preview & QR)
    # ==========================================================
    # Added pady at top to reinforce the gap
    layer_two = ctk.CTkFrame(ROOT, fg_color="transparent")
    layer_two.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
    layer_two.grid_columnconfigure(0, weight=3) # Output takes more space
    layer_two.grid_columnconfigure(1, weight=1) # QR takes less
    layer_two.grid_rowconfigure(0, weight=1)

    # Output Card
    out_frame = ctk.CTkFrame(layer_two, fg_color=COLOR_CARD_BG, corner_radius=12, 
                             border_width=1, border_color=COLOR_BORDER)
    out_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    out_frame.grid_columnconfigure(0, weight=1)
    out_frame.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(out_frame, text="OUTPUT RESULT", font=("Segoe UI", 11, "bold"), 
                 text_color=COLOR_GREEN).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
    
    output_label = ctk.CTkLabel(out_frame, text="Process to view result", 
                               fg_color=COLOR_PREVIEW_BG, corner_radius=8, 
                               text_color=COLOR_TEXT_SECONDARY, font=("Segoe UI", 11))
    output_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

    # QR Card
    qr_frame = ctk.CTkFrame(layer_two, fg_color=COLOR_CARD_BG, corner_radius=12,
                            border_width=1, border_color=COLOR_BORDER)
    qr_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    qr_frame.grid_columnconfigure(0, weight=1)
    qr_frame.grid_rowconfigure(1, weight=1)

    ctk.CTkLabel(qr_frame, text="MOBILE SHARE", font=("Segoe UI", 11, "bold"), 
                 text_color=COLOR_PURPLE).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
    
    qr_code_label = ctk.CTkLabel(qr_frame, text="QR Code", 
                                fg_color=COLOR_PREVIEW_BG, corner_radius=8, 
                                text_color=COLOR_TEXT_SECONDARY, font=("Segoe UI", 10))
    qr_code_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

    # ==========================================================
    # 4. SETTINGS STRIP
    # ==========================================================
    settings_bar = ctk.CTkFrame(ROOT, fg_color=COLOR_CARD_BG, corner_radius=10)
    settings_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
    settings_bar.grid_columnconfigure(3, weight=1) # Push slider to right or center

    # Title
    ctk.CTkLabel(settings_bar, text="SETTINGS", font=("Segoe UI", 10, "bold"), 
                 text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=(15, 10))

    # Options
    _keep_fps_var = ctk.BooleanVar(value=True)
    roop.globals.keep_fps = True
    ctk.CTkCheckBox(settings_bar, text="Keep FPS", variable=_keep_fps_var,
                   command=lambda: setattr(roop.globals, 'keep_fps', _keep_fps_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_CYAN, hover_color=COLOR_CYAN_HOVER,
                   border_width=2).pack(side="left", padx=10, pady=10)

    _skip_audio_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(settings_bar, text="Skip Audio", variable=_skip_audio_var,
                   command=lambda: setattr(roop.globals, 'skip_audio', _skip_audio_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_PINK, hover_color=COLOR_PINK_HOVER,
                   border_width=2).pack(side="left", padx=10, pady=10)

    # Quality Slider (Right aligned in strip)
    qual_frame = ctk.CTkFrame(settings_bar, fg_color="transparent")
    qual_frame.pack(side="right", padx=15, fill="x", expand=True)
    
    qual_val_lbl = ctk.CTkLabel(qual_frame, text="35%", font=("Segoe UI", 11, "bold"), 
                               text_color=COLOR_TEXT_PRIMARY, width=35)
    qual_val_lbl.pack(side="right")

    quality_slider = ctk.CTkSlider(qual_frame, from_=0, to=100, number_of_steps=100,
                                  button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_GREEN)
    quality_slider.set(35)
    quality_slider.pack(side="right", padx=10, fill="x", expand=True)
    
    ctk.CTkLabel(qual_frame, text="Quality", font=("Segoe UI", 11), 
                 text_color=COLOR_TEXT_SECONDARY).pack(side="right")
    
    quality_slider.configure(command=lambda v: (
        setattr(roop.globals, 'output_video_quality', int(v)),
        qual_val_lbl.configure(text=f"{int(v)}%")
    ))

    # ==========================================================
    # 5. ACTION BUTTON (Compact & Sleek)
    # ==========================================================
    # Made button smaller height (45) and added side padding so it's not edge-to-edge
    start_btn = ctk.CTkButton(ROOT, text="START PROCESSING", height=45,
                             command=lambda: file_handlers.select_output_path(start),
                             fg_color=COLOR_GREEN, hover_color=COLOR_GREEN_HOVER,
                             text_color="#000000", font=("Segoe UI", 14, "bold"), 
                             corner_radius=8)
    start_btn.grid(row=4, column=0, sticky="ew", padx=100, pady=(0, 20))


    # References
    file_handlers.init_file_handler_references(ROOT, status_label, _target_label, 
                                              _source_label, output_label, 
                                              qr_code_label, capture_btn)
    camera.init_camera_references(ROOT, _source_label, capture_btn, _camera_switch_var)
    pipeline.init_pipeline_references(ROOT, capture_btn)
    
    if DND_AVAILABLE:
        setup_drag_drop(_source_label, _target_label)
    
    _source_label.bind('<Button-1>', lambda e: file_handlers.select_source_path())
    _target_label.bind('<Button-1>', lambda e: file_handlers.select_target_path())
    
    return ROOT


def create_modern_card(parent, title, accent_color, has_camera):
    """Helper: Create a stylish dark card with neon accent"""
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=12,
                        border_width=1, border_color=COLOR_BORDER)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(1, weight=1)
    
    # Card Header
    header = ctk.CTkFrame(card, fg_color="transparent", height=35)
    header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 5))
    
    # Title with colorful dash
    title_lbl = ctk.CTkLabel(header, text=f"▍ {title}", 
                            font=("Segoe UI", 11, "bold"), text_color=accent_color)
    title_lbl.pack(side="left")
    
    camera_var = None
    if has_camera:
        camera_var = ctk.BooleanVar(value=False)
        cam_switch = ctk.CTkSwitch(header, text="Use Camera", variable=camera_var, 
                                  command=camera.handle_camera_toggle,
                                  progress_color=accent_color, button_color="#fff",
                                  width=40, height=20, font=("Segoe UI", 10))
        cam_switch.pack(side="right")
    
    # Main Preview Area (Recessed)
    preview_label = ctk.CTkLabel(card, 
                                text="DRAG & DROP\nFILE HERE",
                                fg_color=COLOR_PREVIEW_BG, corner_radius=8, 
                                text_color=COLOR_TEXT_SECONDARY, font=("Segoe UI", 10, "bold"))
    preview_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
    
    # Action Button (Outline style or subtle)
    if has_camera:
        btn_text = "📸 Capture Face"
        btn_cmd = lambda: camera.do_capture()
        btn_state = "disabled"
        btn_fg = "#2c3e50"
    else:
        btn_text = "📂 Select File"
        btn_cmd = lambda: file_handlers.select_target_path()
        btn_state = "normal"
        btn_fg = accent_color
    
    action_btn = ctk.CTkButton(card, text=btn_text, height=32,
                              command=btn_cmd, state=btn_state,
                              fg_color="transparent", border_width=2,
                              border_color=btn_fg, hover_color=btn_fg,
                              text_color=COLOR_TEXT_PRIMARY,
                              font=("Segoe UI", 11, "bold"),
                              corner_radius=6)
    action_btn.grid(row=2, column=0, sticky="ew", padx=40, pady=(10, 15))
    
    return {
        'frame': card,
        'label': preview_label,
        'action_btn': action_btn,
        'camera_var': camera_var
    }


def setup_drag_drop(source_label, target_label):
    if not DND_AVAILABLE: return
    source_label.drop_target_register('DND_Files')
    source_label.dnd_bind('<<Drop>>', lambda e: file_handlers.select_source_path(e.data))
    target_label.drop_target_register('DND_Files')
    target_label.dnd_bind('<<Drop>>', lambda e: file_handlers.select_target_path(e.data))

def get_root(): return ROOT
def get_target_label(): return _target_label
def get_source_label(): return _source_label
def get_pipeline_switch_var(): return _pipeline_switch_var
def get_camera_switch_var(): return _camera_switch_var