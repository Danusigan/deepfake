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
temp_frame_quality = 85     # OPTIMIZED: Good quality, faster processing
output_video_encoder = 'libx264'
output_video_quality = 45   # OPTIMIZED: Balanced quality/speed

max_memory = None
execution_providers = ['CUDAExecutionProvider', 'cpu']  # OPTIMIZED: Try GPU first
execution_threads = 4       # OPTIMIZED: Use multiple threads
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
# OPTIMIZED QUALITY SETTINGS FOR SPEED
# ============================================

# Face blending settings - OPTIMIZED
FACE_MASK_BLUR = 10              # OPTIMIZED: Reduced blur for speed
FACE_MASK_PADDING = 0.3          # OPTIMIZED: Less padding
BLEND_RATIO = 0.95               # OPTIMIZED: Slightly reduced

# Enhancement settings - DISABLED FOR SPEED
ENABLE_FACE_ENHANCER = False     # OPTIMIZED: Disabled (biggest speed gain)
FACE_ENHANCER_BLEND = 0.5        
COLOR_CORRECTION = False         # OPTIMIZED: Disabled for speed
SHARPEN_OUTPUT = False           # OPTIMIZED: Disabled for speed

# Face detection - OPTIMIZED
FACE_DETECTION_CONFIDENCE = 0.6  # OPTIMIZED: Slightly higher threshold

# Post-processing - DISABLED FOR SPEED
SMOOTH_EDGES = False             # OPTIMIZED: Disabled for speed
EDGE_BLUR_AMOUNT = 3             

# GIF Processing settings - OPTIMIZED
GIF_QUALITY = 85                 # OPTIMIZED: Reduced from 95
GIF_OPTIMIZE = True              
GIF_PROCESSING_MODE = 'direct'
GIF_MAX_SIZE = 800              # OPTIMIZED: Resize large GIFs for speed
GIF_SKIP_FRAMES = 1             # OPTIMIZED: Process every frame (1) or skip (2+)