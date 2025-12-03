import os

source_path = None
target_path = None
output_path = None

headless = None
frame_processors = ['face_swapper']  # OPTIMIZED: Removed face_enhancer for speed
keep_fps = False
keep_frames = False
skip_audio = False
many_faces = False
reference_face_position = 0
reference_frame_number = 0
similar_face_distance = 0.85

temp_frame_format = 'jpg'  # OPTIMIZED: JPG is faster than PNG
temp_frame_quality = 92     # HIGH QUALITY
output_video_encoder = 'libx264'
output_video_quality = 35   # HIGH QUALITY (lower = better)

max_memory = None
execution_providers = ['CUDAExecutionProvider', 'cpu']  # GPU acceleration
execution_threads = 8       # Multi-threading
log_level = 'error'

FIXED_OUTPUT_DIR = r'C:\Users\sanji\Desktop\Project of Mine all UG\Rextro\deepfake\roop\targets\Outputs'
PIPELINE_ENABLED = False
PIPELINE_AUTO_TARGET = None

if not os.path.exists(FIXED_OUTPUT_DIR):
    try:
        os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)
        print(f"[PIPELINE] Created output directory: {FIXED_OUTPUT_DIR}")
    except Exception as e:
        print(f"[PIPELINE] Error creating output directory: {e}")

# ============================================
# HIGH QUALITY SETTINGS - BALANCED WITH SPEED
# ============================================

# Face blending settings
FACE_MASK_BLUR = 15              # Good quality
FACE_MASK_PADDING = 0.35         # Good coverage
BLEND_RATIO = 0.98               # High blend quality

# Enhancement settings - DISABLED FOR SPEED
ENABLE_FACE_ENHANCER = False     # DISABLED: 4x speed gain
FACE_ENHANCER_BLEND = 0.0        
COLOR_CORRECTION = False         # DISABLED: 2x speed gain
SHARPEN_OUTPUT = False           # DISABLED: Speed gain

# Face detection
FACE_DETECTION_CONFIDENCE = 0.6  

# Post-processing - DISABLED FOR SPEED
SMOOTH_EDGES = False             
EDGE_BLUR_AMOUNT = 0             

# GIF Processing settings - HIGH QUALITY + GOOD SPEED
GIF_QUALITY = 92                 # HIGH QUALITY (was 80)
GIF_OPTIMIZE = True              
GIF_PROCESSING_MODE = 'direct'
GIF_MAX_SIZE = 800              # Don't resize too aggressively
GIF_SKIP_FRAMES = 1             # Process ALL frames for quality (1 = no skip)
GIF_RESIZE_THRESHOLD = 1000     # Only resize very large GIFs

# Video processing
VIDEO_MAX_SIZE = 1080           # HD quality
VIDEO_SKIP_FRAMES = 1           # Process all frames