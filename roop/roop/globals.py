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

FIXED_OUTPUT_DIR = r'E:\Rextro\deepfake\roop\targets\Outputs'
PIPELINE_ENABLED = False
PIPELINE_AUTO_TARGET = None

if not os.path.exists(FIXED_OUTPUT_DIR):
    try:
        os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)
        print(f"[PIPELINE] Created output directory: {FIXED_OUTPUT_DIR}")
    except Exception as e:
        print(f"[PIPELINE] Error creating output directory: {e}")

# ============================================
# PRO DEEPFAKE SETTINGS - LIKE TRENDING SITES
# ============================================

# Face Blending Settings (Professional Quality)
FACE_MASK_BLUR = 15              # Smooth edge blending (1-50)
FACE_MASK_PADDING = 0.35         # Face area coverage (0.0-1.0)
BLEND_RATIO = 0.98               # Face blend strength (0.0-1.0)

# Face Detection Settings
FACE_DETECTION_CONFIDENCE = 0.6  # Face detection threshold
SIMILAR_FACE_DISTANCE = 0.85     # Face similarity threshold

# Enhancement Settings - DISABLED FOR SPEED (Enable for ultra quality)
ENABLE_FACE_ENHANCER = False     # Set True for enhancement (slower)
FACE_ENHANCER_BLEND = 0.0        # Enhancement blend ratio
COLOR_CORRECTION = False         # Auto color correction
SHARPEN_OUTPUT = False           # Output sharpening

# Post-processing - DISABLED FOR SPEED
SMOOTH_EDGES = False             # Edge smoothing
EDGE_BLUR_AMOUNT = 0             # Edge blur radius

# GIF Processing Settings - PROFESSIONAL QUALITY
GIF_QUALITY = 92                 # GIF output quality (50-100)
GIF_OPTIMIZE = True              # Optimize GIF size
GIF_PROCESSING_MODE = 'direct'   # Processing mode
GIF_MAX_SIZE = 800               # Max dimension (pixels)
GIF_SKIP_FRAMES = 1              # Frame skip (1 = no skip)
GIF_RESIZE_THRESHOLD = 1000      # Resize only if larger than this

# Video Processing Settings
VIDEO_MAX_SIZE = 1080            # Max video resolution
VIDEO_SKIP_FRAMES = 1            # Video frame skip

# Advanced Face Swap Settings
FACE_SWAP_MODE = 'best'          # 'fast' or 'best'
PRESERVE_LIGHTING = True         # Match target lighting
PRESERVE_COLOR_TONE = True       # Match target color tone

# Output Settings
OUTPUT_IMAGE_QUALITY = 95        # Image output quality (1-100)
OUTPUT_IMAGE_FORMAT = 'png'      # 'png' or 'jpg'