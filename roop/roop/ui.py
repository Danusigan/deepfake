from typing import Any, Callable, Tuple, Optional
import cv2
import customtkinter as ctk
import os
import sys
import webbrowser
from PIL import Image, ImageOps
from tkinterdnd2 import TkinterDnD, DND_ALL
import time
import tempfile
import glob




# Assuming these imports and global variables are available in the runtime environment
import roop.globals
import roop.metadata
from roop.capturer import get_video_frame, get_video_frame_total
from roop.face_analyser import get_one_face
from roop.face_reference import get_face_reference, set_face_reference, clear_face_reference
from roop.predictor import predict_frame, clear_predictor
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import is_image, is_video, resolve_relative_path
# NEW IMPORT: Must import the new qr_generator file
from roop.qr_generator import generate_qr_code

ROOT = None
ROOT_HEIGHT = 700
ROOT_WIDTH = 1100

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200

RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

# NEW GLOBAL VARIABLES FOR CAMERA
CAPTURER = None
IS_WEBCAM_ACTIVE = False
CAPTURED_FRAME = None # Stores the numpy array of the captured face
WEBCAM_LOOP_ID = None # Stores the ID of the ROOT.after loop

preview_label = None
preview_slider = None
source_label = None
target_label = None
status_label = None
main_frame = None
canvas = None
scrollbar = None
# NEW LABELS
capture_button = None
qr_code_label = None


# todo: remove by native support -> https://github.com/TomSchimansky/CustomTkinter/issues/934
class CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


def init(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global ROOT, PREVIEW, CAPTURER, IS_WEBCAM_ACTIVE

    ROOT = create_root(start, destroy)
    PREVIEW = create_preview(ROOT)

    # Initialize webcam capture
    try:
        CAPTURER = cv2.VideoCapture(0) # 0 for default camera
        if CAPTURER.isOpened():
            IS_WEBCAM_ACTIVE = True
            update_webcam_feed()
            update_status("Webcam connected. Capture your source face!")
        else:
            update_status("Error: Could not open webcam (Index 0). Falling back to file selection.")
            source_label.configure(text="Drag & Drop\nor Click to Select\n\n📸")
            capture_button.configure(text='Webcam Unavailable', state='disabled')
            
    except Exception as e:
        print(f"Webcam initialization error: {e}")
        IS_WEBCAM_ACTIVE = False
        source_label.configure(text="Drag & Drop\nor Click to Select\n\n📸")
        capture_button.configure(text='Webcam Unavailable', state='disabled')

    return ROOT


def create_root(start: Callable[[], None], destroy: Callable[[], None]) -> ctk.CTk:
    global source_label, target_label, status_label, main_frame, canvas, scrollbar, capture_button, qr_code_label

    ctk.deactivate_automatic_dpi_awareness()
    ctk.set_appearance_mode('dark')
    
    try:
        ctk.set_default_color_theme(resolve_relative_path('ui.json'))
    except Exception:
        # Fallback theme if ui.json fails
        ctk.set_default_color_theme("blue")

    root = CTk()
    root.minsize(ROOT_WIDTH, ROOT_HEIGHT)
    root.title(f'{roop.metadata.name} {roop.metadata.version}')
    root.configure()
    # Ensure camera is released on destruction
    root.protocol('WM_DELETE_WINDOW', lambda: (release_webcam(), destroy())) 

    # Create canvas and scrollbar
    canvas = ctk.CTkCanvas(root, highlightthickness=0) 
    scrollbar = ctk.CTkScrollbar(root, orientation="vertical", command=canvas.yview)
    main_frame = ctk.CTkFrame(canvas)

    canvas_window_id = canvas.create_window((0, 0), window=main_frame, anchor="nw")

    main_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    def update_main_frame_width(event):
        canvas.itemconfig(canvas_window_id, width=event.width)

    canvas.bind('<Configure>', update_main_frame_width)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind mouse wheel
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)
    main_frame.bind("<MouseWheel>", _on_mousewheel)
    
    # Bind mousewheel to all child widgets recursively
    def bind_mousewheel_to_children(widget):
        widget.bind("<MouseWheel>", _on_mousewheel)
        for child in widget.winfo_children():
            bind_mousewheel_to_children(child)
    
    # We'll call this after creating all widgets
    def finalize_bindings():
        bind_mousewheel_to_children(main_frame)

    # Header with gradient-like effect - NEW COLOR: Deep Navy/Indigo
    header_frame = ctk.CTkFrame(main_frame, fg_color=("#101828", "#0B111D"), corner_radius=0, height=80)
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
    header_frame.grid_propagate(False)
    
    title_label = ctk.CTkLabel(header_frame, 
                             text=f"🎭 {roop.metadata.name}", 
                             font=("Segoe UI", 32, "bold"),
                             # NEW PRIMARY ACCENT COLOR: Teal/Cyan
                             text_color=("#00FFFF", "#00A8A8"))
    title_label.pack(pady=20)

    # Main content area
    content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    content_frame.grid(row=1, column=0, columnspan=2, padx=30, pady=20, sticky="nsew")

    # Media Upload Section with modern cards
    upload_container = ctk.CTkFrame(content_frame, fg_color="transparent")
    upload_container.pack(fill="x", pady=(0, 20))
    
    upload_container.grid_columnconfigure(0, weight=1)
    upload_container.grid_columnconfigure(1, weight=1)

    # --- Source Card (Modified for Webcam) ---
    source_card = ctk.CTkFrame(upload_container, 
                               fg_color=("#1A2033", "#131826"),
                               corner_radius=20,
                               border_width=2,
                               border_color=("#00FFFF", "#00A8A8"))
    source_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    source_title = ctk.CTkLabel(source_card, 
                                 text="👤 The face you want to swap",
                                 font=("Segoe UI", 18, "bold"),
                                 text_color=("#00FFFF", "#00A8A8"))
    source_title.pack(pady=(20, 10))

    # Webcam/Image Display Label
    source_label = ctk.CTkLabel(source_card, 
                                 text="Initializing Webcam...",
                                 fg_color=("#101828", "#0B111D"),
                                 corner_radius=15,
                                 font=("Segoe UI", 12),
                                 text_color=("gray70", "gray70"),
                                 height=180,
                                 cursor="hand2")
    source_label.pack(padx=20, pady=(0, 10), fill="both", expand=True)
    source_label.drop_target_register(DND_ALL)
    source_label.dnd_bind('<<Drop>>', lambda event: select_source_path(event.data))
    source_label.bind('<Button-1>', lambda e: select_source_path()) # Fallback if webcam fails

    # Capture Button (NEW)
    capture_button = ctk.CTkButton(source_card,
                                   text='📸 Capture Face',
                                   cursor='hand2',
                                   command=capture_source_frame,
                                   fg_color=("#00FFFF", "#00A8A8"),
                                   hover_color=("#00A8A8", "#008585"),
                                   text_color="black",
                                   font=("Segoe UI", 12, "bold"),
                                   corner_radius=10,
                                   height=40)
    capture_button.pack(padx=20, pady=(0, 20), fill="x")
    
    # --- Target Card (Same Logic as before) ---
    target_card = ctk.CTkFrame(upload_container, 
                               fg_color=("#1A2033", "#131826"),
                               corner_radius=20,
                               border_width=2,
                               border_color=("#FF69B4", "#C6438D"))
    target_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    target_title = ctk.CTkLabel(target_card, 
                                 text="🎯 The photo/video want to replace face ",
                                 font=("Segoe UI", 18, "bold"),
                                 text_color=("#FF69B4", "#C6438D"))
    target_title.pack(pady=(20, 10))

    target_label = ctk.CTkLabel(target_card, 
                                 text="Drag & Drop\nor Click to Select\n\n🎬",
                                 fg_color=("#101828", "#0B111D"),
                                 corner_radius=15,
                                 font=("Segoe UI", 12),
                                 text_color=("gray70", "gray70"),
                                 height=180,
                                 cursor="hand2")
    target_label.pack(padx=20, pady=(0, 15), fill="both", expand=True)
    target_label.drop_target_register(DND_ALL)
    target_label.dnd_bind('<<Drop>>', lambda event: select_target_path(event.data))
    target_label.bind('<Button-1>', lambda e: select_target_path())
    
    if roop.globals.target_path:
        select_target_path(roop.globals.target_path)

    target_button = ctk.CTkButton(target_card, 
                                   text='📁 Browse Files',
                                   cursor='hand2',
                                   command=lambda: select_target_path(),
                                   fg_color=("#FF69B4", "#C6438D"),
                                   hover_color=("#C6438D", "#A52A6D"),
                                   text_color="white",
                                   font=("Segoe UI", 12, "bold"),
                                   corner_radius=10,
                                   height=40)
    target_button.pack(padx=20, pady=(0, 20), fill="x")

    # Processing Log (Same Logic as before)
    progress_frame = ctk.CTkFrame(content_frame,
                                  fg_color=("#1A2033", "#131826"),
                                  corner_radius=10,
                                  border_width=1,
                                  border_color=("#00FFFF", "#00A8A8"))
    progress_frame.pack(fill="x", pady=(0, 20))
    
    progress_header = ctk.CTkFrame(progress_frame, fg_color="transparent")
    progress_header.pack(fill="x", padx=15, pady=(10, 5))
    
    ctk.CTkLabel(progress_header,
                 text="📊 Processing Status",
                 font=("Segoe UI", 13, "bold"),
                 text_color=("#00FFFF", "#00A8A8")).pack(side="left")
    
    progress_text = ctk.CTkTextbox(progress_frame,
                                   height=80,
                                   font=("Segoe UI", 10),
                                   fg_color=("#101828", "#0B111D"),
                                   text_color=("#7CFC00", "#7CFC00"), # Bright Green for log success
                                   border_width=0,
                                   wrap="word")
    progress_text.pack(fill="x", padx=15, pady=(0, 10))
    progress_text.insert("1.0", "⚡ Ready - Waiting to start processing...")
    progress_text.configure(state="disabled")
    
    # Store reference globally
    root._progress_text = progress_text

    # Output & QR Code Section (MODIFIED)
    output_preview_frame = ctk.CTkFrame(content_frame,
                                        fg_color=("#1A2033", "#131826"),
                                        corner_radius=15,
                                        border_width=2,
                                        border_color=("#7CFC00", "#6AA84F"))
    output_preview_frame.pack(fill="x", pady=(0, 20))
    
    output_header = ctk.CTkLabel(output_preview_frame,
                                 text="✨ After swapped face & Share QR",
                                 font=("Segoe UI", 16, "bold"),
                                 text_color=("#7CFC00", "#6AA84F"))
    output_header.pack(pady=(20, 10))
    
    output_content_frame = ctk.CTkFrame(output_preview_frame, fg_color="transparent")
    output_content_frame.pack(padx=20, pady=(0, 20), fill="x", expand=True)
    output_content_frame.grid_columnconfigure(0, weight=1)
    output_content_frame.grid_columnconfigure(1, weight=1)

    # Output Display
    output_label = ctk.CTkLabel(output_content_frame,
                                text="Output will appear here\nafter processing",
                                fg_color=("#101828", "#0B111D"),
                                corner_radius=15,
                                font=("Segoe UI", 12),
                                text_color=("gray70", "gray70"),
                                height=250)
    output_label.grid(row=0, column=0, padx=10, sticky="nsew")
    root._output_label = output_label

    # QR Code Display (NEW)
    qr_code_label = ctk.CTkLabel(output_content_frame,
                                text="QR Code for Sharing\n(Scan to Access Output)",
                                fg_color=("#101828", "#0B111D"),
                                corner_radius=15,
                                font=("Segoe UI", 12),
                                text_color=("gray70", "gray70"),
                                height=250)
    qr_code_label.grid(row=0, column=1, padx=10, sticky="nsew")
    
    # Settings Panel, Action Button, Status Label, Footer (retained elements)
    settings_frame = ctk.CTkFrame(content_frame, 
                                  fg_color=("#1A2033", "#131826"),
                                  corner_radius=15)
    settings_frame.pack(fill="x", pady=(0, 20))

    settings_header = ctk.CTkLabel(settings_frame, 
                                     text="⚙️ Advanced Settings",
                                     font=("Segoe UI", 16, "bold"),
                                     text_color=("#00FFFF", "#00A8A8"))
    settings_header.pack(pady=(15, 10), padx=20, anchor="w")

    settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
    settings_grid.pack(fill="x", padx=20, pady=(0, 15))
    
    settings_grid.grid_columnconfigure(0, weight=1)
    settings_grid.grid_columnconfigure(1, weight=1)

    # General Settings
    general_section = ctk.CTkFrame(settings_grid, fg_color=("#101828", "#0B111D"), corner_radius=10)
    general_section.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    ctk.CTkLabel(general_section, text="🎬 Video Options", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    keep_fps_value = ctk.BooleanVar(value=roop.globals.keep_fps)
    keep_fps_switch = ctk.CTkSwitch(general_section, 
                                    text='Keep Original FPS',
                                    variable=keep_fps_value,
                                    cursor='hand2',
                                    command=lambda: setattr(roop.globals, 'keep_fps', keep_fps_value.get()),
                                    progress_color=("#00FFFF", "#00A8A8"))
    keep_fps_switch.pack(pady=5, padx=15, anchor="w")

    skip_audio_value = ctk.BooleanVar(value=roop.globals.skip_audio)
    skip_audio_switch = ctk.CTkSwitch(general_section, 
                                       text='Mute Audio',
                                       variable=skip_audio_value,
                                       cursor='hand2',
                                       command=lambda: setattr(roop.globals, 'skip_audio', skip_audio_value.get()),
                                       progress_color=("#00FFFF", "#00A8A8"))
    skip_audio_switch.pack(pady=5, padx=15, anchor="w")

    keep_frames_value = ctk.BooleanVar(value=roop.globals.keep_frames)
    keep_frames_switch = ctk.CTkSwitch(general_section, 
                                        text='Keep Temp Frames',
                                        variable=keep_frames_value,
                                        cursor='hand2',
                                        command=lambda: setattr(roop.globals, 'keep_frames', keep_frames_value.get()),
                                        progress_color=("#00FFFF", "#00A8A8"))
    keep_frames_switch.pack(pady=(5, 15), padx=15, anchor="w")

    # Face Detection Settings
    face_section = ctk.CTkFrame(settings_grid, fg_color=("#101828", "#0B111D"), corner_radius=10)
    face_section.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    ctk.CTkLabel(face_section, text="👥 Face Detection", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    many_faces_value = ctk.BooleanVar(value=roop.globals.many_faces)
    many_faces_switch = ctk.CTkSwitch(face_section, 
                                       text='Process All Faces',
                                       variable=many_faces_value,
                                       cursor='hand2',
                                       command=lambda: setattr(roop.globals, 'many_faces', many_faces_value.get()),
                                       progress_color=("#FF69B4", "#C6438D"))
    many_faces_switch.pack(pady=5, padx=15, anchor="w")

    ref_frame = ctk.CTkFrame(face_section, fg_color="transparent")
    ref_frame.pack(pady=5, padx=15, fill="x")
    
    ctk.CTkLabel(ref_frame, text="Face Index:", font=("Segoe UI", 11)).pack(side="left")
    reference_entry = ctk.CTkEntry(ref_frame, width=60, placeholder_text="0")
    reference_entry.pack(side="left", padx=(10, 0))
    reference_entry.insert(0, "0")

    ctk.CTkLabel(face_section, 
                 text="Threshold: 0.5", 
                 font=("Segoe UI", 10),
                 text_color="gray60").pack(pady=(5, 15), padx=15, anchor="w")
    
    # Performance Settings
    perf_section = ctk.CTkFrame(settings_grid, fg_color=("#101828", "#0B111D"), corner_radius=10)
    perf_section.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    ctk.CTkLabel(perf_section, text="⚡ Performance", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    thread_frame = ctk.CTkFrame(perf_section, fg_color="transparent")
    thread_frame.pack(pady=5, padx=15, fill="x")
    
    ctk.CTkLabel(thread_frame, text="Threads:", font=("Segoe UI", 11)).pack(anchor="w")
    threads_slider = ctk.CTkSlider(thread_frame, from_=1, to=16, number_of_steps=15,
                                    progress_color=("#00FFFF", "#00A8A8"))
    threads_slider.set(8)
    threads_slider.pack(fill="x", pady=5)

    mem_frame = ctk.CTkFrame(perf_section, fg_color="transparent")
    mem_frame.pack(pady=5, padx=15, fill="x")
    
    ctk.CTkLabel(mem_frame, text="Memory (GB):", font=("Segoe UI", 11)).pack(anchor="w")
    memory_slider = ctk.CTkSlider(mem_frame, from_=1, to=16, number_of_steps=15,
                                    progress_color=("#00FFFF", "#00A8A8"))
    memory_slider.set(4)
    memory_slider.pack(fill="x", pady=(5, 15))

    # Output Settings
    output_section = ctk.CTkFrame(settings_grid, fg_color=("#101828", "#0B111D"), corner_radius=10)
    output_section.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    
    ctk.CTkLabel(output_section, text="💾 Output", font=("Segoe UI", 13, "bold")).pack(pady=(15, 10), padx=15, anchor="w")

    provider_frame = ctk.CTkFrame(output_section, fg_color="transparent")
    provider_frame.pack(pady=5, padx=15, fill="x")
    
    ctk.CTkLabel(provider_frame, text="Provider:", font=("Segoe UI", 11)).pack(anchor="w")
    provider_combobox = ctk.CTkComboBox(provider_frame, 
                                         values=["CPU", "CUDA", "OpenVINO"],
                                         button_color=("#00FFFF", "#00A8A8"),
                                         button_hover_color=("#00A8A8", "#008585"))
    provider_combobox.set("CPU")
    provider_combobox.pack(fill="x", pady=5)

    quality_frame = ctk.CTkFrame(output_section, fg_color="transparent")
    quality_frame.pack(pady=5, padx=15, fill="x")
    
    ctk.CTkLabel(quality_frame, text="Quality (CRF):", font=("Segoe UI", 11)).pack(anchor="w")
    quality_slider = ctk.CTkSlider(quality_frame, from_=0, to=51, number_of_steps=51,
                                    progress_color=("#FF69B4", "#C6438D"))
    quality_slider.set(23)
    quality_slider.pack(fill="x", pady=(5, 15))

    # Action Button
    action_container = ctk.CTkFrame(content_frame, fg_color="transparent")
    action_container.pack(fill="x", pady=(10, 0))

    button_wrapper = ctk.CTkFrame(action_container, fg_color="transparent")
    button_wrapper.pack(anchor="center")

    start_button = ctk.CTkButton(button_wrapper, 
                                 text='🚀 Start Processing',
                                 cursor='hand2',
                                 command=lambda: select_output_path(start),
                                 fg_color=("#7CFC00", "#6AA84F"),
                                 hover_color=("#6AA84F", "#588E3E"),
                                 font=("Segoe UI", 12, "bold"),
                                 text_color="black",
                                 height=40,
                                 width=200,
                                 corner_radius=10)
    start_button.pack(pady=10)

    # Status Label
    status_label = ctk.CTkLabel(action_container, 
                                 text="Ready to process",
                                 font=("Segoe UI", 10),
                                 text_color="gray60")
    status_label.pack(pady=5)

    # Footer
    footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=40)
    footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
    
    footer_label = ctk.CTkLabel(footer_frame, 
                                 text=f"v{roop.metadata.version} | Powered by AI",
                                 font=("Segoe UI", 9),
                                 text_color="gray50")
    footer_label.pack(pady=10)

    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_rowconfigure(1, weight=1)

    # Apply mousewheel binding to all widgets
    finalize_bindings()

    return root


def create_preview(parent: ctk.CTkToplevel) -> ctk.CTkToplevel:
    global preview_label, preview_slider

    preview = ctk.CTkToplevel(parent)
    preview.withdraw()
    preview.configure()
    preview.protocol('WM_DELETE_WINDOW', lambda: toggle_preview())
    preview.resizable(width=False, height=False)

    preview_label = ctk.CTkLabel(preview, text=None)
    preview_label.pack(fill='both', expand=True)

    preview_slider = ctk.CTkSlider(preview, from_=0, to=0, command=lambda frame_value: update_preview(frame_value))

    preview.bind('<Up>', lambda event: update_face_reference(1))
    preview.bind('<Down>', lambda event: update_face_reference(-1))
    return preview

# --- NEW WEBCAM LOGIC ---

def release_webcam() -> None:
    global IS_WEBCAM_ACTIVE, CAPTURER, WEBCAM_LOOP_ID
    
    if WEBCAM_LOOP_ID:
        ROOT.after_cancel(WEBCAM_LOOP_ID)
    
    if CAPTURER and CAPTURER.isOpened():
        CAPTURER.release()
    
    IS_WEBCAM_ACTIVE = False

def capture_source_frame() -> None:
    global IS_WEBCAM_ACTIVE, CAPTURED_FRAME
    
    if not CAPTURER or not CAPTURER.isOpened():
        update_status("Webcam is not active.")
        return

    # Check for latest frame stored by the update loop
    if CAPTURED_FRAME is None:
        update_status("Error: Could not capture frame.")
        return

    # 1. Stop the live feed and prevent re-entry
    if IS_WEBCAM_ACTIVE and WEBCAM_LOOP_ID:
        ROOT.after_cancel(WEBCAM_LOOP_ID)
        IS_WEBCAM_ACTIVE = False
        capture_button.configure(text='🔄 Re-capture Face', fg_color="#FF69B4", hover_color="#C6438D", state='normal')

    # 2. Save the captured frame to a temporary file for roop.globals
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"source_face_captured.png") # Changed filename to be simpler
    
    # Save the NumPy array (CAPTURED_FRAME) to a file
    cv2.imwrite(temp_path, CAPTURED_FRAME)
    
    roop.globals.source_path = temp_path
    
    # 3. Display the static captured frame on the source_label
    image = render_image_preview(roop.globals.source_path, (250, 250))
    source_label.configure(image=image, text="")
    update_status(f"Source face captured from webcam.")


def update_webcam_feed() -> None:
    global CAPTURER, IS_WEBCAM_ACTIVE, CAPTURED_FRAME, WEBCAM_LOOP_ID
    
    if not IS_WEBCAM_ACTIVE or not CAPTURER or not CAPTURER.isOpened():
        return

    # Read a frame from the camera
    has_frame, frame = CAPTURER.read()
    
    if has_frame:
        # Store the raw frame for the capture button
        CAPTURED_FRAME = frame
        
        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        
        # Resize/fit to the preview label size (250x250 defined in create_root)
        size = (250, 250)
        image = ImageOps.fit(image, size, Image.LANCZOS)
        
        # Convert to CTkImage and update label
        ctk_image = ctk.CTkImage(image, size=image.size)
        source_label.configure(image=ctk_image, text="")
        
    # Repeat the loop every 30 milliseconds (approx 33 FPS)
    WEBCAM_LOOP_ID = ROOT.after(30, update_webcam_feed)

# --- END NEW WEBCAM LOGIC ---


def update_status(text: str) -> None:
    """Update the status in the processing log"""
    global status_label
    status_label.configure(text=text)
    
    # Update progress log if available
    if hasattr(ROOT, '_progress_text'):
        progress_text = ROOT._progress_text
        progress_text.configure(state="normal")
        
        # Clear and show only latest status
        progress_text.delete("1.0", "end")
        progress_text.insert("1.0", f"⚡ {text}")
        
        progress_text.configure(state="disabled")
    
    ROOT.update()


def select_source_path(source_path: Optional[str] = None) -> None:
    global RECENT_DIRECTORY_SOURCE, IS_WEBCAM_ACTIVE
    
    # If webcam is active, disable it now since user is choosing a file
    if IS_WEBCAM_ACTIVE and WEBCAM_LOOP_ID:
        ROOT.after_cancel(WEBCAM_LOOP_ID)
        IS_WEBCAM_ACTIVE = False
        if capture_button:
             capture_button.configure(text='Enable Webcam', fg_color="#00FFFF", hover_color="#00A8A8", state='normal', command=lambda: (setattr(globals(), 'IS_WEBCAM_ACTIVE', True), update_webcam_feed(), capture_button.configure(text='📸 Capture Face', command=capture_source_frame, fg_color="#00FFFF")))

    if PREVIEW:
        PREVIEW.withdraw()
    if source_path is None:
        source_path = ctk.filedialog.askopenfilename(
            title='Select source image',
            initialdir=RECENT_DIRECTORY_SOURCE,
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All Files", "*.*")
            ]
        )
    
    # Handle drag and drop - clean the path
    if source_path:
        source_path = source_path.strip('{}').strip()
        
    if source_path and is_image(source_path):
        try:
            roop.globals.source_path = source_path
            RECENT_DIRECTORY_SOURCE = os.path.dirname(roop.globals.source_path)
            image = render_image_preview(roop.globals.source_path, (250, 250))
            source_label.configure(image=image, text="")
        except Exception as e:
            print(f"Error loading source image: {e}")
            roop.globals.source_path = None
            source_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n📸")
    else:
        roop.globals.source_path = None
        source_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n📸")


# --- Gallery UI for Target Selection ---
def show_category_gallery():
    def open_gallery_window(base_folder, media_type):
        win = ctk.CTkToplevel()
        win.title(f"Select a Target ({media_type.title()})")
        win.geometry("900x600")
        # Position window in front of main application
        win.lift()
        win.focus_force()
        win.attributes('-topmost', True)  # Ensure it stays on top

        categories = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
        for cat in categories:
            btn = ctk.CTkButton(win, text=cat.title(), font=("Segoe UI", 18),
                                command=lambda c=cat: show_subcategory(win, base_folder, c, media_type))
            btn.pack(fill='x', padx=10, pady=8)

    def show_subcategory(win, base_folder, category, media_type):
        for widget in win.winfo_children():
            widget.destroy()
        subfolder = os.path.join(base_folder, category)
        subcategories = [d for d in os.listdir(subfolder) if os.path.isdir(os.path.join(subfolder, d))]
        if subcategories:
            for subcat in subcategories:
                btn = ctk.CTkButton(win, text=subcat.title(), font=("Segoe UI", 16),
                                    command=lambda sc=subcat: show_gallery(win, os.path.join(subfolder, sc), media_type))
                btn.pack(fill='x', padx=10, pady=7)
        else:
            show_gallery(win, subfolder, media_type)

    def show_gallery(win, gallery_folder, media_type):
        for widget in win.winfo_children():
            widget.destroy()
        if media_type == 'images':
            filetypes = ('*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif')
        else:
            filetypes = ('*.mp4', '*.avi', '*.mov', '*.mkv')
        files = []
        for ft in filetypes:
            files.extend(glob.glob(os.path.join(gallery_folder, ft)))
        if not files:
            lbl = ctk.CTkLabel(win, text="No files found here.", font=("Segoe UI", 15))
            lbl.pack(pady=20)
            return
        row = 0
        col = 0
        max_cols = 4

        def on_select(path):
            win.destroy()
            roop.globals.target_path = path
            img = render_image_preview(path, (250, 250)) if media_type == 'images' else render_video_preview(path, (250, 250))
            target_label.configure(image=img, text="")
            update_status(f"Selected: {os.path.basename(path)}")

        for idx, fp in enumerate(files):
            thumb = render_image_preview(fp, (120, 120)) if media_type == 'images' else render_video_preview(fp, (120, 120))
            btn = ctk.CTkButton(win, image=thumb, text=os.path.basename(fp), compound='top',
                                command=lambda p=fp: on_select(p), width=140, height=160)
            btn.grid(row=row, column=col, padx=10, pady=14)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    root = ctk.CTkToplevel()
    root.title("Choose Target Type")
    root.geometry("340x260")
    # Position window in front of main application
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)  # Ensure it stays on top

    def choose_type(media_type):
        root.destroy()
        here = os.path.dirname(os.path.abspath(__file__))
        targets_dir = os.path.join(here, '..', 'targets', media_type)
        targets_dir = os.path.abspath(targets_dir)
        if os.path.exists(targets_dir):
            open_gallery_window(targets_dir, media_type)
        else:
            # Fallback to file dialog if gallery folder doesn't exist
            update_status(f"Gallery folder not found: {targets_dir}")
            select_target_path_fallback()

    img_btn = ctk.CTkButton(root, text="Select Image", font=("Segoe UI", 18, "bold"), command=lambda: choose_type('images'))
    vid_btn = ctk.CTkButton(root, text="Select Video", font=("Segoe UI", 18, "bold"), command=lambda: choose_type('videos'))
    img_btn.pack(fill='x', padx=40, pady=(40, 22))
    vid_btn.pack(fill='x', padx=40, pady=(0, 22))
# --- End Gallery UI ---

def select_target_path_fallback():
    """Fallback to traditional file dialog if gallery system fails"""
    global RECENT_DIRECTORY_TARGET
    
    if PREVIEW:
        PREVIEW.withdraw()
    
    target_path = ctk.filedialog.askopenfilename(
        title='Select target media',
        initialdir=RECENT_DIRECTORY_TARGET,
        filetypes=[
            ("All Media Files", "*.jpg *.jpeg *.png *.bmp *.gif *.mp4 *.avi *.mov *.mkv"),
            ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"),
            ("Video Files", "*.mp4 *.avi *.mov *.mkv"),
            ("All Files", "*.*")
        ]
    )
    
    _process_target_path(target_path)


def _process_target_path(target_path: str) -> None:
    """Process the selected target path and update UI"""
    global RECENT_DIRECTORY_TARGET
    
    # Handle drag and drop - clean the path
    if target_path:
        # Remove curly braces and extra whitespace that may come from drag-drop
        target_path = target_path.strip('{}').strip()
        
    if target_path and is_image(target_path):
        try:
            roop.globals.target_path = target_path
            RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
            image = render_image_preview(roop.globals.target_path, (250, 250))
            target_label.configure(image=image, text="")
            update_status(f"Selected image: {os.path.basename(target_path)}")
        except Exception as e:
            print(f"Error loading target image: {e}")
            roop.globals.target_path = None
            target_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n🎬")
    elif target_path and is_video(target_path):
        try:
            roop.globals.target_path = target_path
            RECENT_DIRECTORY_TARGET = os.path.dirname(roop.globals.target_path)
            video_frame = render_video_preview(target_path, (250, 250))
            target_label.configure(image=video_frame, text="")
            update_status(f"Selected video: {os.path.basename(target_path)}")
        except Exception as e:
            print(f"Error loading target video: {e}")
            roop.globals.target_path = None
            target_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n🎬")
    else:
        roop.globals.target_path = None
        target_label.configure(image=None, text="Drag & Drop\nor Click to Select\n\n🎬")


def select_target_path(target_path: Optional[str] = None) -> None:
    global RECENT_DIRECTORY_TARGET
    if target_path:
        # For drag-and-drop or manual input, behave as before
        if PREVIEW:
            PREVIEW.withdraw()
        clear_face_reference()
        _process_target_path(target_path)
    else:
        # Use your new gallery UI when no file path is given
        show_category_gallery()


def select_output_path(start: Callable[[], None]) -> None:
    global RECENT_DIRECTORY_OUTPUT

    if is_image(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='Save output image', defaultextension='.png', initialfile='output.png', initialdir=RECENT_DIRECTORY_OUTPUT)
    elif is_video(roop.globals.target_path):
        output_path = ctk.filedialog.asksaveasfilename(title='Save output video', defaultextension='.mp4', initialfile='output.mp4', initialdir=RECENT_DIRECTORY_OUTPUT)
    else:
        output_path = None
    if output_path:
        roop.globals.output_path = output_path
        RECENT_DIRECTORY_OUTPUT = os.path.dirname(roop.globals.output_path)
        start()
        
        # After processing completes, try to show output preview (moved QR logic to core.py after validation)
        try:
            if hasattr(ROOT, '_output_label') and os.path.exists(output_path):
                if is_image(output_path):
                    output_image = render_image_preview(output_path, (400, 400))
                    ROOT._output_label.configure(image=output_image, text="")
                elif is_video(output_path):
                    output_frame = render_video_preview(output_path, (400, 400))
                    ROOT._output_label.configure(image=output_frame, text="")
        except Exception as e:
            print(f"Could not display output preview: {e}")

# --- NEW QR GENERATION FUNCTION ---
def generate_qr_for_output(output_path: str) -> None:
    """Uploads the file and generates a QR code pointing to the shareable URL."""
    global qr_code_label

    # --- SIMULATED SHARING LOGIC ---
    # In a real app, this is where you would call your Firebase Storage upload function.
    # E.g., shared_url = upload_to_firebase_storage(output_path)

    # SIMULATION: Use a placeholder URL that mentions the output file name
    shared_url = f"https://share.roop-output.com/{os.path.basename(output_path)}"

    # Display the simulated sharing URL and generate QR code
    qr_code_label.configure(text=f"Scan QR to download/view:\n{os.path.basename(output_path)}", text_color=("#7CFC00", "#6AA84F"))
    
    try:
        # Generate and display the QR code image
        qr_image = generate_qr_code(shared_url, (200, 200)) 
        qr_code_label.configure(image=qr_image, text="")
    except Exception as e:
        print(f"Error generating QR code: {e}")
        qr_code_label.configure(image=None, text="QR Code Failed")


def render_image_preview(image_path: str, size: Tuple[int, int]) -> ctk.CTkImage:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return ctk.CTkImage(image, size=image.size)


def render_video_preview(video_path: str, size: Tuple[int, int], frame_number: int = 0) -> ctk.CTkImage:
    capture = cv2.VideoCapture(video_path)
    if frame_number:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    has_frame, frame = capture.read()
    if has_frame:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        capture.release()
        return ctk.CTkImage(image, size=image.size)
    capture.release()
    cv2.destroyAllWindows()


def toggle_preview() -> None:
    if PREVIEW.state() == 'normal':
        PREVIEW.unbind('<Right>')
        PREVIEW.unbind('<Left>')
        PREVIEW.withdraw()
        clear_predictor()
    elif roop.globals.source_path and roop.globals.target_path:
        init_preview()
        update_preview(roop.globals.reference_frame_number)
        PREVIEW.deiconify()


def init_preview() -> None:
    PREVIEW.title('Preview [ ↕ Reference face ]')
    if is_image(roop.globals.target_path):
        preview_slider.pack_forget()
    if is_video(roop.globals.target_path):
        video_frame_total = get_video_frame_total(roop.globals.target_path)
        if video_frame_total > 0:
            PREVIEW.title('Preview [ ↕ Reference face ] [ ↔ Frame number ]')
            PREVIEW.bind('<Right>', lambda event: update_frame(int(video_frame_total / 20)))
            PREVIEW.bind('<Left>', lambda event: update_frame(int(video_frame_total / -20)))
        preview_slider.configure(to=video_frame_total)
        preview_slider.pack(fill='x')
        preview_slider.set(roop.globals.reference_frame_number)


def update_preview(frame_number: int = 0) -> None:
    if roop.globals.source_path and roop.globals.target_path:
        temp_frame = get_video_frame(roop.globals.target_path, frame_number)
        if predict_frame(temp_frame):
            sys.exit()
        source_face = get_one_face(cv2.imread(roop.globals.source_path))
        if not get_face_reference():
            reference_frame = get_video_frame(roop.globals.target_path, roop.globals.reference_frame_number)
            reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
            set_face_reference(reference_face)
        else:
            reference_face = get_face_reference()
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            temp_frame = frame_processor.process_frame(
                source_face,
                reference_face,
                temp_frame
            )
        image = Image.fromarray(cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB))
        image = ImageOps.contain(image, (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.LANCZOS)
        image = ctk.CTkImage(image, size=image.size)
        preview_label.configure(image=image)


def update_face_reference(steps: int) -> None:
    clear_face_reference()
    reference_frame_number = int(preview_slider.get())
    roop.globals.reference_face_position += steps
    roop.globals.reference_frame_number = reference_frame_number
    update_preview(reference_frame_number)


def update_frame(steps: int) -> None:
    frame_number = preview_slider.get() + steps
    preview_slider.set(frame_number)
    update_preview(preview_slider.get())