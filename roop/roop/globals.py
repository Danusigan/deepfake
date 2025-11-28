import os

source_path = None
target_path = None
output_path = None

headless = None
frame_processors = ['face_swapper', 'face_enhancer']  # CHANGED: Added face_enhancer
keep_fps = False
keep_frames = False
skip_audio = False
many_faces = False
reference_face_position = 0
reference_frame_number = 0
similar_face_distance = 0.85

temp_frame_format = 'png'
temp_frame_quality = 0
output_video_encoder = 'libx264'
output_video_quality = 35

max_memory = None
execution_providers = ['cpu']
execution_threads = 1
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
# ENHANCED QUALITY SETTINGS - NEW
# ============================================

# Face blending settings for better quality
FACE_MASK_BLUR = 20              # Blur amount for smooth edges (1-50)
FACE_MASK_PADDING = 0.4          # Padding around face (0.0-1.0)
BLEND_RATIO = 1.0                # Face blend ratio (0.8-1.0)

# Enhancement settings
ENABLE_FACE_ENHANCER = True      # Use GFPGAN for face enhancement
FACE_ENHANCER_BLEND = 0.8        # Enhancement strength (0.0-1.0)
COLOR_CORRECTION = True          # Match skin tone to target
SHARPEN_OUTPUT = True            # Sharpen final result

# Face detection
FACE_DETECTION_CONFIDENCE = 0.5  # Lower = detect more faces (0.0-1.0)

# Post-processing
SMOOTH_EDGES = True              # Smooth face edges
EDGE_BLUR_AMOUNT = 5            # Edge smoothing amount (1-20)

# GIF Processing settings
GIF_QUALITY = 95                # GIF output quality (0-100)
GIF_OPTIMIZE = True             # Optimize GIF file size
GIF_PROCESSING_MODE = 'direct'  # 'direct' or 'video'