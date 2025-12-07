#!/usr/bin/env python3

import os
import sys
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
from typing import List
import platform
import signal
import shutil
import argparse
import time
import requests
import cv2
import numpy as np
import onnxruntime
import tensorflow
import roop.globals
import roop.metadata
# Fix UI import
try:
    import roop.ui as ui
except ImportError as e:
    print(f"UI import error: {e}")
    # Fallback for headless mode
    ui = None
from roop.predictor import predict_image, predict_video
from roop.processors.frame.core import get_frame_processors_modules
from roop.utilities import has_image_extension, is_image, is_video, detect_fps, create_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clean_temp, normalize_output_path
from roop.supabase_utils import upload_image_and_generate_qr
from roop.face_analyser import get_one_face

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


def parse_args() -> None:
    signal.signal(signal.SIGINT, lambda signal_number, frame: destroy())
    program = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=100))
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or video', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='frame processors (choices: face_swapper, face_enhancer, ...)', dest='frame_processor', default=['face_swapper'], nargs='+')
    program.add_argument('--keep-fps', help='keep target fps', dest='keep_fps', action='store_true')
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true')
    program.add_argument('--skip-audio', help='skip target audio', dest='skip_audio', action='store_true')
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true')
    program.add_argument('--reference-face-position', help='position of the reference face', dest='reference_face_position', type=int, default=0)
    program.add_argument('--reference-frame-number', help='number of the reference frame', dest='reference_frame_number', type=int, default=0)
    program.add_argument('--similar-face-distance', help='face distance used for recognition', dest='similar_face_distance', type=float, default=0.85)
    program.add_argument('--temp-frame-format', help='image format used for frame extraction', dest='temp_frame_format', default='png', choices=['jpg', 'png'])
    program.add_argument('--temp-frame-quality', help='image quality used for frame extraction', dest='temp_frame_quality', type=int, default=0, choices=range(101), metavar='[0-100]')
    program.add_argument('--output-video-encoder', help='encoder used for the output video', dest='output_video_encoder', default='libx264', choices=['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc'])
    program.add_argument('--output-video-quality', help='quality used for the output video', dest='output_video_quality', type=int, default=35, choices=range(101), metavar='[0-100]')
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int)
    program.add_argument('--execution-provider', help='available execution provider (choices: cpu, ...)', dest='execution_provider', default=['cpu'], choices=suggest_execution_providers(), nargs='+')
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int, default=suggest_execution_threads())
    program.add_argument('-v', '--version', action='version', version=f'{roop.metadata.name} {roop.metadata.version}')

    args = program.parse_args()

    roop.globals.source_path = args.source_path
    roop.globals.target_path = args.target_path
    roop.globals.output_path = normalize_output_path(roop.globals.source_path, roop.globals.target_path, args.output_path)
    roop.globals.headless = roop.globals.source_path is not None and roop.globals.target_path is not None and roop.globals.output_path is not None
    roop.globals.frame_processors = args.frame_processor
    roop.globals.keep_fps = args.keep_fps
    roop.globals.keep_frames = args.keep_frames
    roop.globals.skip_audio = args.skip_audio
    roop.globals.many_faces = args.many_faces
    roop.globals.reference_face_position = args.reference_face_position
    roop.globals.reference_frame_number = args.reference_frame_number
    roop.globals.similar_face_distance = args.similar_face_distance
    roop.globals.temp_frame_format = args.temp_frame_format
    roop.globals.temp_frame_quality = args.temp_frame_quality
    roop.globals.output_video_encoder = args.output_video_encoder
    roop.globals.output_video_quality = args.output_video_quality
    roop.globals.max_memory = args.max_memory
    roop.globals.execution_providers = decode_execution_providers(args.execution_provider)
    roop.globals.execution_threads = args.execution_threads


def encode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [execution_provider.replace('ExecutionProvider', '').lower() for execution_provider in execution_providers]


def decode_execution_providers(execution_providers: List[str]) -> List[str]:
    return [provider for provider, encoded_execution_provider in zip(onnxruntime.get_available_providers(), encode_execution_providers(onnxruntime.get_available_providers()))
             if any(execution_provider in encoded_execution_provider for execution_provider in execution_providers)]


def suggest_execution_providers() -> List[str]:
    return encode_execution_providers(onnxruntime.get_available_providers())


def suggest_execution_threads() -> int:
    if 'CUDAExecutionProvider' in onnxruntime.get_available_providers():
        return 8
    return 1


def limit_resources() -> None:
    gpus = tensorflow.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tensorflow.config.experimental.set_virtual_device_configuration(gpu, [
            tensorflow.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)
        ])
    if roop.globals.max_memory:
        memory = roop.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = roop.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def pre_check() -> bool:
    if sys.version_info < (3, 9):
        update_status('Python version is not supported - please upgrade to 3.9 or higher.')
        return False
    if not shutil.which('ffmpeg'):
        update_status('ffmpeg is not installed.')
        return False
    return True


def update_status(message: str, scope: str = 'ROOP.CORE') -> None:
    print(f'[{scope}] {message}')
    if not roop.globals.headless and ui:
        ui.update_status(message)


def is_gif(path: str) -> bool:
    """Check if file is a GIF"""
    return path and path.lower().endswith('.gif')

def process_gif(source_path: str, target_gif_path: str, output_path: str) -> None:
    """Process GIF - HIGH QUALITY with speed optimizations"""
    from PIL import Image, ImageSequence
    
    update_status('Processing GIF in HIGH QUALITY mode...')
    
    # Open target GIF
    target_gif = Image.open(target_gif_path)
    
    # Get original dimensions
    original_size = target_gif.size
    
    # Smart resize: Only resize VERY large GIFs
    max_size = roop.globals.GIF_MAX_SIZE if hasattr(roop.globals, 'GIF_MAX_SIZE') else 800
    resize_threshold = roop.globals.GIF_RESIZE_THRESHOLD if hasattr(roop.globals, 'GIF_RESIZE_THRESHOLD') else 1000
    
    if original_size[0] > resize_threshold or original_size[1] > resize_threshold:
        ratio = min(max_size / original_size[0], max_size / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        update_status(f'Resizing for speed: {original_size} → {new_size}')
    else:
        new_size = original_size
        update_status(f'Processing at original size: {new_size[0]}x{new_size[1]}')
    
    # Load source face ONCE
    update_status('Loading source face...')
    source_face = get_one_face(cv2.imread(source_path))
    
    if source_face is None:
        update_status('❌ No face detected in source!')
        return
    
    update_status('✅ Source face loaded')
    
    processed_frames = []
    frame_delays = []
    faces_found = 0
    
    try:
        # Get frame count
        frame_count = 0
        try:
            while True:
                target_gif.seek(frame_count)
                frame_count += 1
        except EOFError:
            pass
        
        target_gif.seek(0)
        
        # Smart frame skipping: Only skip for VERY long GIFs
        skip_frames = roop.globals.GIF_SKIP_FRAMES if hasattr(roop.globals, 'GIF_SKIP_FRAMES') else 1
        
        if frame_count > 200:
            skip_frames = 2
            update_status(f'Very long GIF ({frame_count} frames) - processing every 2nd frame')
        elif frame_count > 100:
            update_status(f'Processing all {frame_count} frames (may take time)')
        else:
            update_status(f'Processing all {frame_count} frames')
        
        frames_to_process = (frame_count + skip_frames - 1) // skip_frames
        
        frame_idx = 0
        processed_count = 0
        
        for frame in ImageSequence.Iterator(target_gif):
            # Skip frames if needed
            if frame_idx % skip_frames != 0:
                frame_idx += 1
                continue
            
            processed_count += 1
            
            # Update status every 5 frames
            if processed_count % 5 == 0:
                update_status(f'Processing frame {processed_count}/{frames_to_process}...')
            
            # Convert and resize
            frame_rgb = frame.convert('RGB')
            if frame_rgb.size != new_size:
                frame_rgb = frame_rgb.resize(new_size, Image.LANCZOS)
            
            frame_array = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            # Face detection and swap
            target_face = get_one_face(frame_bgr)
            
            if target_face is not None:
                faces_found += 1
                for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
                    frame_bgr = frame_processor.process_frame(source_face, target_face, frame_bgr)
            
            # Convert back to PIL
            frame_rgb_processed = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb_processed.astype('uint8'))
            processed_frames.append(pil_frame)
            
            # Frame delay
            try:
                delay = frame.info.get('duration', 100)
                if skip_frames > 1:
                    delay *= skip_frames
                if delay < 20:
                    delay = 20
                frame_delays.append(delay)
            except:
                frame_delays.append(100)
            
            frame_idx += 1
        
        update_status(f'Detected {faces_found} faces | Saving HIGH QUALITY GIF...')
        
        # Save with HIGH QUALITY settings
        gif_quality = roop.globals.GIF_QUALITY if hasattr(roop.globals, 'GIF_QUALITY') else 92
        
        processed_frames[0].save(
            output_path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=frame_delays,
            loop=0,
            optimize=True,
            quality=gif_quality,
        )
        
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        update_status(f'✅ HIGH QUALITY GIF complete! {len(processed_frames)} frames, {output_size_mb:.2f}MB')
        
    except Exception as e:
        update_status(f'❌ GIF error: {e}')
        import traceback
        traceback.print_exc()
        raise

def start() -> None:
    print("[DEBUG] start() function called")
    
    if not roop.globals.source_path:
        update_status('Error: Please select or capture a source image/face.')
        return

    if not roop.globals.target_path:
        update_status('Error: Please select target media.')
        return

    if roop.globals.PIPELINE_ENABLED:
        timestamp = int(time.time())
        
        # FIXED: Proper extension detection for GIF
        if is_gif(roop.globals.target_path):
            ext = '.gif'
        elif has_image_extension(roop.globals.target_path):
            ext = '.png'
        elif is_video(roop.globals.target_path):
            ext = '.mp4'
        else:
            update_status('Error: Invalid target file type.')
            return
        
        output_filename = f"output_{timestamp}{ext}"
        roop.globals.output_path = os.path.join(roop.globals.FIXED_OUTPUT_DIR, output_filename)
        
        update_status(f'Pipeline: Saving to {output_filename}')
        print(f"[DEBUG] Pipeline output path: {roop.globals.output_path}")
    
    if not roop.globals.output_path:
        update_status('Error: Output path not set.')
        return

    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    
    # ADDED: Handle GIF processing
    if is_gif(roop.globals.target_path):
        print("[DEBUG] Processing GIF")
        try:
            process_gif(roop.globals.source_path, roop.globals.target_path, roop.globals.output_path)
            
            if os.path.exists(roop.globals.output_path):
                print(f"[DEBUG] GIF output created: {roop.globals.output_path}")
                update_status('✅ GIF processing complete!')
                if ui:
                    print("[DEBUG] Calling ui.check_and_display_output for GIF")
                    ui.check_and_display_output(roop.globals.output_path)
            else:
                print("[DEBUG] GIF output file not found!")
                update_status('Processing to GIF failed!')
        except Exception as e:
            print(f"[ERROR] GIF processing error: {e}")
            import traceback
            traceback.print_exc()
            update_status(f'GIF processing error: {e}')
        return
    
    # Handle image processing
    if has_image_extension(roop.globals.target_path):
        print("[DEBUG] Processing Image")
        if predict_image(roop.globals.target_path):
            destroy()
        shutil.copy2(roop.globals.target_path, roop.globals.output_path)
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_image(roop.globals.source_path, roop.globals.output_path, roop.globals.output_path)
            frame_processor.post_process()
        if is_image(roop.globals.output_path):
            print(f"[DEBUG] Image output created: {roop.globals.output_path}")
            update_status('✅ Image processing complete!')
            
            # Auto-upload to Supabase
            try:
                with open(roop.globals.output_path, 'rb') as f:
                    image_bytes = f.read()
                upload_result = upload_image_and_generate_qr(image_bytes, os.path.basename(roop.globals.output_path))
                update_status(f'✅ Image uploaded to Supabase!')
                update_status(f'📷 Image URL: {upload_result["url"]}')
                update_status(f'🔗 QR URL: {upload_result["qr_url"]}')
                
                # Store URLs for UI QR generation
                if ui and hasattr(ui, 'file_handlers'):
                    ui.file_handlers.store_supabase_urls(upload_result["url"], upload_result["qr_url"])
                
                # Save QR code locally for display
                qr_local_path = roop.globals.output_path.replace('.png', '_qr.png')
                try:
                    qr_bytes = requests.get(upload_result["qr_url"]).content
                    with open(qr_local_path, 'wb') as f:
                        f.write(qr_bytes)
                    update_status(f'💾 QR code saved to: {qr_local_path}')
                except Exception as qr_err:
                    update_status(f'⚠️ Could not download QR: {qr_err}')
                
            except Exception as e:
                update_status(f'❌ Supabase upload failed: {e}')
                import traceback
                traceback.print_exc()
            
            if ui:
                print("[DEBUG] Calling ui.check_and_display_output for Image")
                ui.check_and_display_output(roop.globals.output_path)
        else:
            print("[DEBUG] Image output file not found!")
            update_status('Processing to image failed!')
        return
    
    # Handle video processing
    print("[DEBUG] Processing Video")
    if predict_video(roop.globals.target_path):
        destroy()
    update_status('Creating temporary resources...')
    create_temp(roop.globals.target_path)
    if roop.globals.keep_fps:
        fps = detect_fps(roop.globals.target_path)
        update_status(f'Extracting frames with {fps} FPS...')
        extract_frames(roop.globals.target_path, fps)
    else:
        update_status('Extracting frames with 30 FPS...')
        extract_frames(roop.globals.target_path)
    temp_frame_paths = get_temp_frame_paths(roop.globals.target_path)
    if temp_frame_paths:
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_video(roop.globals.source_path, temp_frame_paths)
            frame_processor.post_process()
    else:
        update_status('Frames not found...')
        return
    if roop.globals.keep_fps:
        fps = detect_fps(roop.globals.target_path)
        update_status(f'Creating video with {fps} FPS...')
        create_video(roop.globals.target_path, fps)
    else:
        update_status('Creating video with 30 FPS...')
        create_video(roop.globals.target_path)
    if roop.globals.skip_audio:
        move_temp(roop.globals.target_path, roop.globals.output_path)
        update_status('Skipping audio...')
    else:
        if roop.globals.keep_fps:
            update_status('Restoring audio...')
        else:
            update_status('Restoring audio might cause issues as fps are not kept...')
        restore_audio(roop.globals.target_path, roop.globals.output_path)
    update_status('Cleaning temporary resources...')
    clean_temp(roop.globals.target_path)
    if is_video(roop.globals.output_path):
        print(f"[DEBUG] Video output created: {roop.globals.output_path}")
        update_status('✅ Video processing complete!')
        
        # Auto-upload video to Supabase
        try:
            with open(roop.globals.output_path, 'rb') as f:
                video_bytes = f.read()
            upload_result = upload_image_and_generate_qr(video_bytes, os.path.basename(roop.globals.output_path))
            update_status(f'✅ Video uploaded to Supabase!')
            update_status(f'🎬 Video URL: {upload_result["url"]}')
            update_status(f'🔗 QR URL: {upload_result["qr_url"]}')
            
            # Store URLs for UI QR generation
            if ui and hasattr(ui, 'file_handlers'):
                ui.file_handlers.store_supabase_urls(upload_result["url"], upload_result["qr_url"])
            
            # Save QR code locally
            qr_local_path = roop.globals.output_path.replace('.mp4', '_qr.png')
            try:
                qr_bytes = requests.get(upload_result["qr_url"]).content
                with open(qr_local_path, 'wb') as f:
                    f.write(qr_bytes)
                update_status(f'💾 QR code saved to: {qr_local_path}')
            except Exception as qr_err:
                update_status(f'⚠️ Could not download QR: {qr_err}')
        except Exception as e:
            update_status(f'❌ Supabase upload failed: {e}')
            import traceback
            traceback.print_exc()
        
        if ui:
            print("[DEBUG] Calling ui.check_and_display_output for Video")
            ui.check_and_display_output(roop.globals.output_path)
    else:
        print("[DEBUG] Video output file not found!")
        update_status('Processing to video failed!')


def destroy() -> None:
    if ui and hasattr(ui, 'destroy_camera'):
        ui.destroy_camera()
    if roop.globals.target_path:
        clean_temp(roop.globals.target_path)
    sys.exit()


def run() -> None:
    parse_args()
    if not pre_check():
        return
    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        if not frame_processor.pre_check():
            return
    limit_resources()
    if roop.globals.headless:
        start()
    else:
        if ui:
            window = ui.init(start, destroy)
            window.mainloop()
        else:
            print("UI not available. Running in headless mode requires source, target, and output paths.")