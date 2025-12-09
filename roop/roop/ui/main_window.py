"""
Main window module - Ultra Modern Scrollable Design with Gradient Accents
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

# --- ULTRA MODERN COLOR PALETTE (Like Reface, Deepfake.com, FaceSwap Live) ---
COLOR_BG = "#0a0e1a"          # Deep dark navy
COLOR_HEADER_BG = "#0f1419"   # Darker header
COLOR_CARD_BG = "#141824"     # Card background
COLOR_PREVIEW_BG = "#0d1117"  # Preview background
COLOR_BORDER = "#1e2736"      # Subtle border

# Vibrant Neon Gradients
COLOR_CYAN = "#00f2fe"        # Electric cyan
COLOR_CYAN_HOVER = "#00d4ea"
COLOR_CYAN_DARK = "#0088cc"

COLOR_PINK = "#ff0080"        # Hot pink
COLOR_PINK_HOVER = "#e6006f"
COLOR_PINK_LIGHT = "#ff3399"

COLOR_PURPLE = "#bf40ff"      # Vivid purple
COLOR_PURPLE_HOVER = "#a020f0"

COLOR_GREEN = "#00ff88"       # Neon green
COLOR_GREEN_HOVER = "#00e673"

COLOR_ORANGE = "#ff6b35"      # Vibrant orange

COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#a0aec0"
COLOR_TEXT_MUTED = "#64748b"

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
    ROOT.state('zoomed')
    ROOT.title(f'{roop.metadata.name} {roop.metadata.version} - Pro Edition')
    ROOT.geometry('1100x900')
    ROOT.configure(fg_color=COLOR_BG)
    ROOT.resizable(True, True)
    
    # === MAIN CONTAINER - SCROLLABLE ===
    ROOT.grid_columnconfigure(0, weight=1)
    ROOT.grid_rowconfigure(0, weight=0)  # Header (Fixed)
    ROOT.grid_rowconfigure(1, weight=1)  # Scrollable Content (Expands)

    # ==========================================================
    # 1. FIXED HEADER BAR (Glassmorphism Style)
    # ==========================================================
    header_frame = ctk.CTkFrame(ROOT, fg_color=COLOR_HEADER_BG, corner_radius=0, height=70)
    header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    header_frame.grid_columnconfigure(1, weight=1)
    header_frame.grid_propagate(False)

    # Brand with Gradient Effect
    brand_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
    brand_frame.grid(row=0, column=0, padx=25, pady=15)
    
    title_label = ctk.CTkLabel(brand_frame, text="🎭 ROOP", 
                               font=("Segoe UI", 22, "bold"), 
                               text_color=COLOR_CYAN)
    title_label.pack(side="left")
    
    pro_badge = ctk.CTkLabel(brand_frame, text="PRO", 
                            font=("Segoe UI", 10, "bold"),
                            text_color=COLOR_BG,
                            fg_color=COLOR_PINK,
                            corner_radius=4,
                            padx=8, pady=2)
    pro_badge.pack(side="left", padx=(8, 0))

    # Status (Center) with Glow Effect - SIMPLIFIED
    status_container = ctk.CTkFrame(header_frame, fg_color="#1a1f2e", corner_radius=20, 
                                   border_width=1, border_color=COLOR_GREEN,
                                   height=36)
    status_container.grid(row=0, column=1)
    status_container.grid_propagate(False)
    
    status_inner = ctk.CTkFrame(status_container, fg_color="transparent")
    status_inner.pack(padx=20, pady=0, expand=True)
    
    status_icon = ctk.CTkLabel(status_inner, text="●", font=("Segoe UI", 14), 
                              text_color=COLOR_GREEN)
    status_icon.pack(side="left", padx=(0, 8))
    
    status_label = ctk.CTkLabel(status_inner, text="Ready to Process", 
                                font=("Segoe UI", 12, "bold"), 
                                text_color=COLOR_TEXT_PRIMARY)
    status_label.pack(side="left")

    # Pipeline Toggle (Right) - Modern Switch
    pipeline_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    pipeline_container.grid(row=0, column=2, padx=25)
    
    _pipeline_switch_var = ctk.BooleanVar(value=roop.globals.PIPELINE_ENABLED)
    pipe_switch = ctk.CTkSwitch(
        pipeline_container, 
        text="🤖 Auto Mode", 
        variable=_pipeline_switch_var, 
        command=pipeline.handle_pipeline_toggle, 
        progress_color=COLOR_PINK,
        button_color=COLOR_TEXT_PRIMARY,
        font=("Segoe UI", 12, "bold"),
        text_color=COLOR_TEXT_PRIMARY,
        fg_color="#2d3748",
        width=60,
        height=28
    )
    pipe_switch.pack()

    # ==========================================================
    # 2. SCROLLABLE MAIN CONTENT (OPTIMIZED)
    # ==========================================================
    scroll_container = ctk.CTkScrollableFrame(ROOT, fg_color="transparent", 
                                              corner_radius=0,
                                              scrollbar_button_color=COLOR_CYAN,
                                              scrollbar_button_hover_color=COLOR_CYAN_HOVER)
    scroll_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
    scroll_container.grid_columnconfigure(0, weight=1)
    
    # Add padding with simple frame
    content_wrapper = ctk.CTkFrame(scroll_container, fg_color="transparent")
    content_wrapper.pack(fill="both", expand=True, padx=30, pady=30)
    content_wrapper.grid_columnconfigure(0, weight=1)

    # ==========================================================
    # 3. INPUT SECTION (Source & Target) - BIGGER CARDS
    # ==========================================================
    input_section = ctk.CTkFrame(content_wrapper, fg_color="transparent")
    input_section.pack(fill="x", pady=(0, 30))
    input_section.grid_columnconfigure(0, weight=1)
    input_section.grid_columnconfigure(1, weight=1)

    # Source Card - EXPANDED
    source_card = create_premium_card(input_section, "SOURCE FACE", COLOR_CYAN, True, 550)
    source_card['frame'].grid(row=0, column=0, sticky="nsew", padx=(0, 15))
    _source_label = source_card['label']
    _camera_switch_var = source_card['camera_var']
    capture_btn = source_card['action_btn']

    # Target Card - EXPANDED
    target_card = create_premium_card(input_section, "TARGET MEDIA", COLOR_PINK, False, 550)
    target_card['frame'].grid(row=0, column=1, sticky="nsew", padx=(15, 0))
    _target_label = target_card['label']

    # ==========================================================
    # 4. OUTPUT SECTION (Result & QR) - EQUAL SIZES
    # ==========================================================
    output_section = ctk.CTkFrame(content_wrapper, fg_color="transparent")
    output_section.pack(fill="x", pady=(0, 30))
    output_section.grid_columnconfigure(0, weight=1)
    output_section.grid_columnconfigure(1, weight=1)

    # Output Card - EXPANDED & EQUAL
    output_card = create_output_card(output_section, "OUTPUT RESULT", COLOR_GREEN, 550)
    output_card['frame'].grid(row=0, column=0, sticky="nsew", padx=(0, 15))
    output_label = output_card['label']

    # QR Card - EXPANDED & EQUAL SIZE
    qr_card = create_qr_card(output_section, 550)
    qr_card['frame'].grid(row=0, column=1, sticky="nsew", padx=(15, 0))
    qr_code_label = qr_card['label']

    # ==========================================================
    # 5. SETTINGS SECTION (Beautiful Organized Panels)
    # ==========================================================
    settings_section = ctk.CTkFrame(content_wrapper, fg_color=COLOR_CARD_BG, 
                                   corner_radius=20, border_width=1, 
                                   border_color=COLOR_BORDER)
    settings_section.pack(fill="x", pady=(0, 30))
    
    # Settings Header
    settings_header = ctk.CTkFrame(settings_section, fg_color="transparent", height=60)
    settings_header.pack(fill="x", padx=25, pady=(20, 15))
    settings_header.pack_propagate(False)
    
    header_left = ctk.CTkFrame(settings_header, fg_color="transparent")
    header_left.pack(side="left", fill="y")
    
    ctk.CTkLabel(header_left, text="⚡ ADVANCED SETTINGS", 
                font=("Segoe UI", 16, "bold"), 
                text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    
    ctk.CTkLabel(header_left, text="Fine-tune your deepfake quality", 
                font=("Segoe UI", 11), 
                text_color=COLOR_TEXT_MUTED).pack(side="left", padx=(15, 0))

    # Settings Grid
    settings_grid = ctk.CTkFrame(settings_section, fg_color="transparent")
    settings_grid.pack(fill="x", padx=25, pady=(0, 25))
    settings_grid.grid_columnconfigure(0, weight=1)
    settings_grid.grid_columnconfigure(1, weight=1)

    # LEFT COLUMN
    left_col = ctk.CTkFrame(settings_grid, fg_color="transparent")
    left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

    # ===== GENERAL SETTINGS PANEL =====
    general_panel_container = ctk.CTkFrame(left_col, fg_color="#1a1f2e", corner_radius=15,
                                          border_width=1, border_color=COLOR_BORDER)
    general_panel_container.pack(fill="x", pady=(0, 20))
    
    # Header
    gen_header = ctk.CTkFrame(general_panel_container, fg_color="transparent")
    gen_header.pack(fill="x", padx=20, pady=(15, 10))
    
    ctk.CTkLabel(gen_header, text="● ⚙️ GENERAL", font=("Segoe UI", 12, "bold"), 
                text_color=COLOR_CYAN).pack(side="left")
    
    ctk.CTkFrame(gen_header, fg_color=COLOR_CYAN, height=2).pack(fill="x", pady=(8, 0))
    
    # Content
    gen_content = ctk.CTkFrame(general_panel_container, fg_color="transparent")
    gen_content.pack(fill="x", padx=20, pady=(0, 15))
    
    _many_faces_var = ctk.BooleanVar(value=roop.globals.many_faces)
    ctk.CTkCheckBox(gen_content, text="Process All Faces in Frame", 
                   variable=_many_faces_var,
                   command=lambda: setattr(roop.globals, 'many_faces', _many_faces_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_CYAN, 
                   hover_color=COLOR_CYAN_HOVER,
                   border_width=2, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=6)
    
    _keep_frames_var = ctk.BooleanVar(value=roop.globals.keep_frames)
    ctk.CTkCheckBox(gen_content, text="Keep Temporary Frames", 
                   variable=_keep_frames_var,
                   command=lambda: setattr(roop.globals, 'keep_frames', _keep_frames_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_PURPLE, 
                   hover_color=COLOR_PURPLE_HOVER,
                   border_width=2, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=6)

    # ===== FACE QUALITY PANEL =====
    face_panel_container = ctk.CTkFrame(left_col, fg_color="#1a1f2e", corner_radius=15,
                                       border_width=1, border_color=COLOR_BORDER)
    face_panel_container.pack(fill="x", pady=(0, 20))
    
    # Header
    face_header = ctk.CTkFrame(face_panel_container, fg_color="transparent")
    face_header.pack(fill="x", padx=20, pady=(15, 10))
    
    ctk.CTkLabel(face_header, text="● 👤 FACE QUALITY", font=("Segoe UI", 12, "bold"), 
                text_color=COLOR_PINK).pack(side="left")
    
    ctk.CTkFrame(face_header, fg_color=COLOR_PINK, height=2).pack(fill="x", pady=(8, 0))
    
    # Content
    face_content = ctk.CTkFrame(face_panel_container, fg_color="transparent")
    face_content.pack(fill="x", padx=20, pady=(0, 15))
    
    # Mask Blur Slider
    blur_frame = ctk.CTkFrame(face_content, fg_color="transparent")
    blur_frame.pack(fill="x", pady=8)
    
    blur_top = ctk.CTkFrame(blur_frame, fg_color="transparent")
    blur_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(blur_top, text="Face Mask Blur", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    blur_val_lbl = ctk.CTkLabel(blur_top, text="15", font=("Segoe UI", 10, "bold"), 
                               text_color=COLOR_TEXT_PRIMARY)
    blur_val_lbl.pack(side="right")
    
    blur_slider = ctk.CTkSlider(blur_frame, from_=1, to=50, number_of_steps=49,
                               button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_PINK,
                               height=16)
    blur_slider.set(15)
    blur_slider.pack(fill="x")
    blur_slider.configure(command=lambda v: (
        setattr(roop.globals, 'FACE_MASK_BLUR', int(v)),
        blur_val_lbl.configure(text=str(int(v)))
    ))
    
    # Mask Padding Slider
    pad_frame = ctk.CTkFrame(face_content, fg_color="transparent")
    pad_frame.pack(fill="x", pady=8)
    
    pad_top = ctk.CTkFrame(pad_frame, fg_color="transparent")
    pad_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(pad_top, text="Face Mask Padding", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    pad_val_lbl = ctk.CTkLabel(pad_top, text="0.35", font=("Segoe UI", 10, "bold"), 
                              text_color=COLOR_TEXT_PRIMARY)
    pad_val_lbl.pack(side="right")
    
    pad_slider = ctk.CTkSlider(pad_frame, from_=0.0, to=1.0, number_of_steps=100,
                              button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_PINK,
                              height=16)
    pad_slider.set(0.35)
    pad_slider.pack(fill="x")
    pad_slider.configure(command=lambda v: (
        setattr(roop.globals, 'FACE_MASK_PADDING', float(v)),
        pad_val_lbl.configure(text=f"{float(v):.2f}")
    ))
    
    # Blend Ratio Slider
    blend_frame = ctk.CTkFrame(face_content, fg_color="transparent")
    blend_frame.pack(fill="x", pady=8)
    
    blend_top = ctk.CTkFrame(blend_frame, fg_color="transparent")
    blend_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(blend_top, text="Blend Ratio", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    blend_val_lbl = ctk.CTkLabel(blend_top, text="0.98", font=("Segoe UI", 10, "bold"), 
                                text_color=COLOR_TEXT_PRIMARY)
    blend_val_lbl.pack(side="right")
    
    blend_slider = ctk.CTkSlider(blend_frame, from_=0.0, to=1.0, number_of_steps=100,
                                button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_PINK,
                                height=16)
    blend_slider.set(0.98)
    blend_slider.pack(fill="x")
    blend_slider.configure(command=lambda v: (
        setattr(roop.globals, 'BLEND_RATIO', float(v)),
        blend_val_lbl.configure(text=f"{float(v):.2f}")
    ))
    
    # Detection Confidence Slider
    det_frame = ctk.CTkFrame(face_content, fg_color="transparent")
    det_frame.pack(fill="x", pady=8)
    
    det_top = ctk.CTkFrame(det_frame, fg_color="transparent")
    det_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(det_top, text="Detection Confidence", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    det_val_lbl = ctk.CTkLabel(det_top, text="0.60", font=("Segoe UI", 10, "bold"), 
                              text_color=COLOR_TEXT_PRIMARY)
    det_val_lbl.pack(side="right")
    
    det_slider = ctk.CTkSlider(det_frame, from_=0.1, to=1.0, number_of_steps=90,
                              button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_PINK,
                              height=16)
    det_slider.set(0.6)
    det_slider.pack(fill="x")
    det_slider.configure(command=lambda v: (
        setattr(roop.globals, 'FACE_DETECTION_CONFIDENCE', float(v)),
        det_val_lbl.configure(text=f"{float(v):.2f}")
    ))

    # ===== VIDEO PANEL =====
    video_panel_container = ctk.CTkFrame(left_col, fg_color="#1a1f2e", corner_radius=15,
                                        border_width=1, border_color=COLOR_BORDER)
    video_panel_container.pack(fill="x")
    
    # Header
    vid_header = ctk.CTkFrame(video_panel_container, fg_color="transparent")
    vid_header.pack(fill="x", padx=20, pady=(15, 10))
    
    ctk.CTkLabel(vid_header, text="● 🎬 VIDEO", font=("Segoe UI", 12, "bold"), 
                text_color=COLOR_GREEN).pack(side="left")
    
    ctk.CTkFrame(vid_header, fg_color=COLOR_GREEN, height=2).pack(fill="x", pady=(8, 0))
    
    # Content
    vid_content = ctk.CTkFrame(video_panel_container, fg_color="transparent")
    vid_content.pack(fill="x", padx=20, pady=(0, 15))
    
    _keep_fps_var = ctk.BooleanVar(value=True)
    roop.globals.keep_fps = True
    ctk.CTkCheckBox(vid_content, text="Keep Original FPS", 
                   variable=_keep_fps_var,
                   command=lambda: setattr(roop.globals, 'keep_fps', _keep_fps_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_GREEN, 
                   hover_color=COLOR_GREEN_HOVER,
                   border_width=2, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=6)
    
    _skip_audio_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(vid_content, text="Remove Audio Track", 
                   variable=_skip_audio_var,
                   command=lambda: setattr(roop.globals, 'skip_audio', _skip_audio_var.get()),
                   font=("Segoe UI", 11), fg_color=COLOR_ORANGE, 
                   hover_color="#e55a25",
                   border_width=2, text_color=COLOR_TEXT_SECONDARY).pack(anchor="w", pady=6)
    
    # Video Quality Slider
    vq_frame = ctk.CTkFrame(vid_content, fg_color="transparent")
    vq_frame.pack(fill="x", pady=8)
    
    vq_top = ctk.CTkFrame(vq_frame, fg_color="transparent")
    vq_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(vq_top, text="Video Quality (Lower=Better)", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    vq_val_lbl = ctk.CTkLabel(vq_top, text="35", font=("Segoe UI", 10, "bold"), 
                             text_color=COLOR_TEXT_PRIMARY)
    vq_val_lbl.pack(side="right")
    
    vq_slider = ctk.CTkSlider(vq_frame, from_=0, to=100, number_of_steps=100,
                             button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_GREEN,
                             height=16)
    vq_slider.set(35)
    vq_slider.pack(fill="x")
    vq_slider.configure(command=lambda v: (
        setattr(roop.globals, 'output_video_quality', int(v)),
        vq_val_lbl.configure(text=str(int(v)))
    ))
    
    # Video Resolution Slider
    vr_frame = ctk.CTkFrame(vid_content, fg_color="transparent")
    vr_frame.pack(fill="x", pady=8)
    
    vr_top = ctk.CTkFrame(vr_frame, fg_color="transparent")
    vr_top.pack(fill="x", pady=(0, 5))
    ctk.CTkLabel(vr_top, text="Max Resolution", font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    vr_val_lbl = ctk.CTkLabel(vr_top, text="1080", font=("Segoe UI", 10, "bold"), 
                             text_color=COLOR_TEXT_PRIMARY)
    vr_val_lbl.pack(side="right")
    
    vr_slider = ctk.CTkSlider(vr_frame, from_=480, to=1920, number_of_steps=144,
                             button_color=COLOR_TEXT_PRIMARY, progress_color=COLOR_GREEN,
                             height=16)
    vr_slider.set(1080)
    vr_slider.pack(fill="x")
    vr_slider.configure(command=lambda v: (
        setattr(roop.globals, 'VIDEO_MAX_SIZE', int(v)),
        vr_val_lbl.configure(text=str(int(v)))
    ))

    # RIGHT COLUMN
    right_col = ctk.CTkFrame(settings_grid, fg_color="transparent")
    right_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

    # GIF Settings Panel
    gif_panel = create_settings_panel(right_col, "🎞️ GIF PROCESSING", COLOR_PURPLE)
    gif_panel.pack(fill="x", pady=(0, 20))
    
    # GIF Quality
    gq_container = ctk.CTkFrame(gif_panel, fg_color="transparent")
    gq_container.pack(fill="x", pady=8, padx=10)
    
    gq_label_frame = ctk.CTkFrame(gq_container, fg_color="transparent")
    gq_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(gq_label_frame, text="GIF Output Quality", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    gq_val = ctk.CTkLabel(gq_label_frame, text="92", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    gq_val.pack(side="right")
    
    gq_slider = ctk.CTkSlider(gq_container, from_=50, to=100, number_of_steps=50,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_PURPLE,
                             height=16, button_length=20)
    gq_slider.set(92)
    gq_slider.pack(fill="x")
    gq_slider.configure(command=lambda v: (
        setattr(roop.globals, 'GIF_QUALITY', int(v)),
        gq_val.configure(text=str(int(v)))
    ))
    
    # GIF Max Size
    gs_container = ctk.CTkFrame(gif_panel, fg_color="transparent")
    gs_container.pack(fill="x", pady=8, padx=10)
    
    gs_label_frame = ctk.CTkFrame(gs_container, fg_color="transparent")
    gs_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(gs_label_frame, text="GIF Max Dimension (pixels)", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    gs_val = ctk.CTkLabel(gs_label_frame, text="800", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    gs_val.pack(side="right")
    
    gs_slider = ctk.CTkSlider(gs_container, from_=400, to=1200, number_of_steps=80,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_PURPLE,
                             height=16, button_length=20)
    gs_slider.set(800)
    gs_slider.pack(fill="x")
    gs_slider.configure(command=lambda v: (
        setattr(roop.globals, 'GIF_MAX_SIZE', int(v)),
        gs_val.configure(text=str(int(v)))
    ))
    
    # GIF Frame Skip
    gf_container = ctk.CTkFrame(gif_panel, fg_color="transparent")
    gf_container.pack(fill="x", pady=8, padx=10)
    
    gf_label_frame = ctk.CTkFrame(gf_container, fg_color="transparent")
    gf_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(gf_label_frame, text="Frame Skip (1 = No Skip)", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    gf_val = ctk.CTkLabel(gf_label_frame, text="1", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    gf_val.pack(side="right")
    
    gf_slider = ctk.CTkSlider(gf_container, from_=1, to=5, number_of_steps=4,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_PURPLE,
                             height=16, button_length=20)
    gf_slider.set(1)
    gf_slider.pack(fill="x")
    gf_slider.configure(command=lambda v: (
        setattr(roop.globals, 'GIF_SKIP_FRAMES', int(v)),
        gf_val.configure(text=str(int(v)))
    ))

    # Image Settings Panel
    image_panel = create_settings_panel(right_col, "🖼️ IMAGE OUTPUT", COLOR_CYAN)
    image_panel.pack(fill="x", pady=(0, 20))
    
    # Image Quality
    iq_container = ctk.CTkFrame(image_panel, fg_color="transparent")
    iq_container.pack(fill="x", pady=8, padx=10)
    
    iq_label_frame = ctk.CTkFrame(iq_container, fg_color="transparent")
    iq_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(iq_label_frame, text="Image Quality", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    iq_val = ctk.CTkLabel(iq_label_frame, text="95", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    iq_val.pack(side="right")
    
    iq_slider = ctk.CTkSlider(iq_container, from_=70, to=100, number_of_steps=30,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_CYAN,
                             height=16, button_length=20)
    iq_slider.set(95)
    iq_slider.pack(fill="x")
    iq_slider.configure(command=lambda v: (
        setattr(roop.globals, 'OUTPUT_IMAGE_QUALITY', int(v)),
        iq_val.configure(text=str(int(v)))
    ))
    
    # Temp Frame Quality
    tq_container = ctk.CTkFrame(image_panel, fg_color="transparent")
    tq_container.pack(fill="x", pady=8, padx=10)
    
    tq_label_frame = ctk.CTkFrame(tq_container, fg_color="transparent")
    tq_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(tq_label_frame, text="Temp Frame Quality", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    tq_val = ctk.CTkLabel(tq_label_frame, text="92", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    tq_val.pack(side="right")
    
    tq_slider = ctk.CTkSlider(tq_container, from_=0, to=100, number_of_steps=100,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_CYAN,
                             height=16, button_length=20)
    tq_slider.set(92)
    tq_slider.pack(fill="x")
    tq_slider.configure(command=lambda v: (
        setattr(roop.globals, 'temp_frame_quality', int(v)),
        tq_val.configure(text=str(int(v)))
    ))

    # Advanced Processing Panel
    advanced_panel = create_settings_panel(right_col, "🔬 ADVANCED", COLOR_ORANGE)
    advanced_panel.pack(fill="x")
    
    # Similarity Threshold
    st_container = ctk.CTkFrame(advanced_panel, fg_color="transparent")
    st_container.pack(fill="x", pady=8, padx=10)
    
    st_label_frame = ctk.CTkFrame(st_container, fg_color="transparent")
    st_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(st_label_frame, text="Face Similarity Threshold", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    st_val = ctk.CTkLabel(st_label_frame, text="0.85", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    st_val.pack(side="right")
    
    st_slider = ctk.CTkSlider(st_container, from_=0.1, to=1.0, number_of_steps=90,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_ORANGE,
                             height=16, button_length=20)
    st_slider.set(0.85)
    st_slider.pack(fill="x")
    st_slider.configure(command=lambda v: (
        setattr(roop.globals, 'similar_face_distance', float(v)),
        st_val.configure(text=f"{float(v):.2f}")
    ))
    
    # Execution Threads
    et_container = ctk.CTkFrame(advanced_panel, fg_color="transparent")
    et_container.pack(fill="x", pady=8, padx=10)
    
    et_label_frame = ctk.CTkFrame(et_container, fg_color="transparent")
    et_label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(et_label_frame, text="CPU Threads", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    et_val = ctk.CTkLabel(et_label_frame, text="8", 
                         font=("Segoe UI", 10, "bold"), 
                         text_color=COLOR_TEXT_PRIMARY)
    et_val.pack(side="right")
    
    et_slider = ctk.CTkSlider(et_container, from_=1, to=16, number_of_steps=15,
                             button_color=COLOR_TEXT_PRIMARY, 
                             progress_color=COLOR_ORANGE,
                             height=16, button_length=20)
    et_slider.set(8)
    et_slider.pack(fill="x")
    et_slider.configure(command=lambda v: (
        setattr(roop.globals, 'execution_threads', int(v)),
        et_val.configure(text=str(int(v)))
    ))
    
    # Enhancement toggles
    enhance_var = ctk.BooleanVar(value=getattr(roop.globals, 'ENABLE_FACE_ENHANCER', False))
    cb5 = ctk.CTkCheckBox(advanced_panel, text="Enable Face Enhancement (Slower)", 
                         variable=enhance_var,
                         command=lambda: setattr(roop.globals, 'ENABLE_FACE_ENHANCER', enhance_var.get()),
                         font=("Segoe UI", 11), fg_color=COLOR_ORANGE, 
                         hover_color="#e55a25",
                         border_width=2, corner_radius=6,
                         text_color=COLOR_TEXT_SECONDARY)
    cb5.pack(anchor="w", pady=6, padx=10)
    
    color_var = ctk.BooleanVar(value=getattr(roop.globals, 'COLOR_CORRECTION', False))
    cb6 = ctk.CTkCheckBox(advanced_panel, text="Auto Color Correction", 
                         variable=color_var,
                         command=lambda: setattr(roop.globals, 'COLOR_CORRECTION', color_var.get()),
                         font=("Segoe UI", 11), fg_color=COLOR_ORANGE, 
                         hover_color="#e55a25",
                         border_width=2, corner_radius=6,
                         text_color=COLOR_TEXT_SECONDARY)
    cb6.pack(anchor="w", pady=6, padx=10)

    # ==========================================================
    # 6. ACTION BUTTON (Gradient Style)
    # ==========================================================
    action_container = ctk.CTkFrame(content_wrapper, fg_color="transparent")
    action_container.pack(fill="x", pady=(0, 30))
    
    start_btn = ctk.CTkButton(action_container, 
                             text="🚀 START PROCESSING",
                             height=60,
                             command=lambda: file_handlers.select_output_path(start),
                             fg_color=COLOR_GREEN, 
                             hover_color=COLOR_GREEN_HOVER,
                             text_color=COLOR_BG, 
                             font=("Segoe UI", 16, "bold"), 
                             corner_radius=15,
                             border_width=0)
    start_btn.pack(fill="x", padx=100)

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
    
    # Force render all widgets
    ROOT.update_idletasks()
    scroll_container.update_idletasks()
    
    return ROOT


def create_premium_card(parent, title, accent_color, has_camera, height=550):
    """Create premium card with gradient accent"""
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=20,
                       border_width=2, border_color=COLOR_BORDER, height=height)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(1, weight=1)
    card.grid_propagate(False)
    
    # Header with gradient line
    header_container = ctk.CTkFrame(card, fg_color="transparent")
    header_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
    header_container.grid_columnconfigure(0, weight=1)
    
    # Title with icon
    title_frame = ctk.CTkFrame(header_container, fg_color="transparent")
    title_frame.grid(row=0, column=0, sticky="w")
    
    ctk.CTkLabel(title_frame, text="●", font=("Segoe UI", 20), 
                text_color=accent_color).pack(side="left", padx=(0, 8))
    
    ctk.CTkLabel(title_frame, text=title, 
                font=("Segoe UI", 14, "bold"), 
                text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    
    # Camera switch if needed
    camera_var = None
    if has_camera:
        camera_var = ctk.BooleanVar(value=False)
        cam_switch = ctk.CTkSwitch(header_container, text="📷 Camera", 
                                  variable=camera_var, 
                                  command=camera.handle_camera_toggle,
                                  progress_color=accent_color,
                                  button_color=COLOR_TEXT_PRIMARY,
                                  font=("Segoe UI", 11, "bold"),
                                  text_color=COLOR_TEXT_SECONDARY,
                                  fg_color="#2d3748")
        cam_switch.grid(row=0, column=1, sticky="e")
    
    # Gradient line
    gradient_line = ctk.CTkFrame(header_container, fg_color=accent_color, 
                                height=2, corner_radius=1)
    gradient_line.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    
    # Preview Area with glow effect - EXPANDED
    preview_container = ctk.CTkFrame(card, fg_color=COLOR_PREVIEW_BG, 
                                    corner_radius=15)
    preview_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    preview_container.grid_columnconfigure(0, weight=1)
    preview_container.grid_rowconfigure(0, weight=1)
    
    preview_label = ctk.CTkLabel(preview_container, 
                                text="DRAG & DROP\nOR CLICK HERE",
                                fg_color="transparent",
                                text_color=COLOR_TEXT_MUTED, 
                                font=("Segoe UI", 11, "bold"))
    preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    # Action Button
    if has_camera:
        btn_text = "📸 Capture Face"
        btn_cmd = lambda: camera.do_capture()
        btn_state = "disabled"
        btn_fg = "#2d3748"
    else:
        btn_text = "📂 Browse Files"
        btn_cmd = lambda: file_handlers.select_target_path()
        btn_state = "normal"
        btn_fg = accent_color
    
    action_btn = ctk.CTkButton(card, text=btn_text, height=40,
                              command=btn_cmd, state=btn_state,
                              fg_color=btn_fg, hover_color=accent_color,
                              text_color=COLOR_TEXT_PRIMARY,
                              font=("Segoe UI", 12, "bold"),
                              corner_radius=12,
                              border_width=0)
    action_btn.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
    
    return {
        'frame': card,
        'label': preview_label,
        'action_btn': action_btn,
        'camera_var': camera_var
    }


def create_output_card(parent, title, accent_color, height=550):
    """Create output preview card - EXPANDED"""
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=20,
                       border_width=2, border_color=COLOR_BORDER, height=height)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(1, weight=1)
    card.grid_propagate(False)
    
    # Header
    header = ctk.CTkFrame(card, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
    
    ctk.CTkLabel(header, text="●", font=("Segoe UI", 20), 
                text_color=accent_color).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(header, text=title, font=("Segoe UI", 14, "bold"), 
                text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    
    # Preview
    preview_label = ctk.CTkLabel(card, text="Result will appear here",
                                fg_color=COLOR_PREVIEW_BG, corner_radius=15,
                                text_color=COLOR_TEXT_MUTED, 
                                font=("Segoe UI", 11))
    preview_label.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
    
    return {'frame': card, 'label': preview_label}


def create_qr_card(parent, height=550):
    """Create QR code card - SAME SIZE AS OUTPUT (EXPANDED)"""
    card = ctk.CTkFrame(parent, fg_color=COLOR_CARD_BG, corner_radius=20,
                       border_width=2, border_color=COLOR_BORDER, height=height)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(0, weight=1)
    card.grid_propagate(False)
    
    # Center content
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.grid(row=0, column=0)
    
    # Icon header
    icon_frame = ctk.CTkFrame(content, fg_color="transparent")
    icon_frame.pack(pady=(20, 15))
    
    ctk.CTkLabel(icon_frame, text="📱", font=("Segoe UI", 32)).pack()
    
    # Title
    ctk.CTkLabel(content, text="SCAN TO VIEW", 
                font=("Segoe UI", 14, "bold"), 
                text_color=COLOR_PURPLE).pack(pady=(0, 15))
    
    # QR Code - LARGER (380x380 to fit expanded card)
    qr_label = ctk.CTkLabel(content, text="QR Code\nWill Appear\nHere",
                           fg_color=COLOR_PREVIEW_BG, corner_radius=15,
                           text_color=COLOR_TEXT_MUTED, font=("Segoe UI", 10),
                           width=380, height=380)
    qr_label.pack(pady=(0, 15))
    
    # Helper text
    ctk.CTkLabel(content, text="Scan with your phone camera", 
                font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_MUTED).pack()
    
    return {'frame': card, 'label': qr_label}


def create_settings_panel(parent, title, accent_color):
    """Create modern settings panel with proper sizing - FIXED"""
    panel = ctk.CTkFrame(parent, fg_color="#1a1f2e", corner_radius=15,
                        border_width=1, border_color=COLOR_BORDER)
    
    # Header
    header = ctk.CTkFrame(panel, fg_color="transparent", height=40)
    header.pack(fill="x", padx=20, pady=(15, 10))
    header.pack_propagate(False)
    
    # Title with colored bullet
    title_container = ctk.CTkFrame(header, fg_color="transparent")
    title_container.pack(anchor="w", expand=True)
    
    ctk.CTkLabel(title_container, text="●", font=("Segoe UI", 12), 
                text_color=accent_color).pack(side="left", padx=(0, 8))
    
    ctk.CTkLabel(title_container, text=title, font=("Segoe UI", 12, "bold"), 
                text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    
    # Thin accent line
    ctk.CTkFrame(header, fg_color=accent_color, height=2, 
                corner_radius=1).pack(fill="x", side="bottom")
    
    # Content area with minimum height
    content = ctk.CTkFrame(panel, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=20, pady=(5, 15))
    
    # Force immediate render
    panel.update_idletasks()
    
    return content


def create_checkbox(parent, text, variable, color, command):
    """Create styled checkbox - FIXED"""
    cb = ctk.CTkCheckBox(parent, text=text, variable=variable,
                        command=command, font=("Segoe UI", 11),
                        fg_color=color, hover_color=color,
                        border_width=2, corner_radius=6,
                        text_color=COLOR_TEXT_SECONDARY)
    cb.pack(anchor="w", pady=6, padx=5)
    return cb


def create_slider(parent, label, from_val, to_val, default, color, command, is_float=False):
    """Create styled slider with label - FIXED"""
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="x", pady=8, padx=5)
    
    # Label and value
    label_frame = ctk.CTkFrame(container, fg_color="transparent")
    label_frame.pack(fill="x", pady=(0, 5))
    
    ctk.CTkLabel(label_frame, text=label, font=("Segoe UI", 10), 
                text_color=COLOR_TEXT_SECONDARY).pack(side="left")
    
    if is_float:
        val_text = f"{default:.2f}"
    else:
        val_text = str(int(default))
    
    val_label = ctk.CTkLabel(label_frame, text=val_text, 
                            font=("Segoe UI", 10, "bold"), 
                            text_color=COLOR_TEXT_PRIMARY)
    val_label.pack(side="right")
    
    # Slider
    steps = 100 if is_float else int(to_val - from_val)
    slider = ctk.CTkSlider(container, from_=from_val, to=to_val, 
                          number_of_steps=steps,
                          button_color=COLOR_TEXT_PRIMARY, 
                          progress_color=color,
                          height=16, button_length=20)
    slider.set(default)
    slider.pack(fill="x")
    
    def on_change(v):
        command(v)
        if is_float:
            val_label.configure(text=f"{float(v):.2f}")
        else:
            val_label.configure(text=str(int(v)))
    
    slider.configure(command=on_change)
    
    # Force update to show slider
    container.update_idletasks()
    
    return slider


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