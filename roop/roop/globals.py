import os

source_path = None
target_path = None
output_path = None

headless = None
frame_processors = []
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