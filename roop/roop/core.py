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
    """Process GIF file frame by frame and save as HIGH QUALITY GIF"""
    from PIL import Image, ImageSequence
    
    update_status('Processing GIF in HIGH QUALITY mode...')
    
    # Open target GIF
    target_gif = Image.open(target_gif_path)
    
    # Get original dimensions
    original_size = target_gif.size
    update_status(f'Original GIF size: {original_size[0]}x{original_size[1]}')
    
    # CRITICAL: Load source face ONCE before processing
    update_status('Loading source face...')
    source_face = get_one_face(cv2.imread(source_path))
    
    if source_face is None:
        update_status('❌ ERROR: No face detected in source image!')
        update_status('Please use a clear image with a visible face.')
        return
    
    update_status('✅ Source face loaded successfully')
    
    processed_frames = []
    frame_delays = []
    faces_found = 0
    faces_missing = 0
    
    try:
        # Get total frame count
        frame_count = 0
        try:
            while True:
                target_gif.seek(frame_count)
                frame_count += 1
        except EOFError:
            pass
        
        target_gif.seek(0)  # Reset to first frame
        update_status(f'Processing {frame_count} frames...')
        
        for frame_idx, frame in enumerate(ImageSequence.Iterator(target_gif)):
            update_status(f'Processing frame {frame_idx + 1}/{frame_count}...')
            
            # Convert PIL frame to RGB (preserve quality)
            frame_rgb = frame.convert('RGB')
            
            # Resize to maintain quality if needed
            if frame_rgb.size != original_size:
                frame_rgb = frame_rgb.resize(original_size, Image.LANCZOS)
            
            frame_array = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            # CRITICAL: Detect face in current GIF frame
            target_face = get_one_face(frame_bgr)
            
            # Process frame with face swapper ONLY if face is detected
            if target_face is not None:
                faces_found += 1
                for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
                    frame_bgr = frame_processor.process_frame(
                        source_face,   # Source face (pre-loaded)
                        target_face,   # Target face from current frame
                        frame_bgr      # Current frame to process
                    )
            else:
                faces_missing += 1
                if faces_missing <= 3:  # Only show first 3 warnings
                    update_status(f'⚠️ No face detected in frame {frame_idx + 1}, keeping original')
            
            # Convert back to PIL Image (maintain quality)
            frame_rgb_processed = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb_processed.astype('uint8'))
            
            processed_frames.append(pil_frame)
            
            # Get frame delay (duration)
            try:
                delay = frame.info.get('duration', 100)
                # Ensure minimum delay for smooth playback
                if delay < 20:
                    delay = 20
                frame_delays.append(delay)
            except:
                frame_delays.append(100)
        
        # Report face detection stats
        update_status(f'Face detection: {faces_found} faces found, {faces_missing} frames without faces')
        
        if faces_found == 0:
            update_status('❌ WARNING: No faces detected in any GIF frames!')
            update_status('The GIF will be saved but faces were NOT swapped.')
        
        # Save as HIGH QUALITY animated GIF
        update_status('Saving HIGH QUALITY GIF (this may take a moment)...')
        
        processed_frames[0].save(
            output_path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=frame_delays,
            loop=0,
            optimize=True,  # Enable optimization
            quality=95,     # High quality (0-100, higher is better)
        )
        
        update_status(f'✅ HIGH QUALITY GIF complete! {len(processed_frames)} frames')
        
        # Show file size info
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        update_status(f'Output size: {output_size_mb:.2f} MB')
        
    except Exception as e:
        update_status(f'❌ Error processing GIF: {e}')
        import traceback
        traceback.print_exc()
        raise


def process_gif_as_video(source_path: str, target_gif_path: str, output_path: str) -> None:
    """
    ALTERNATIVE: Process GIF as video for BEST QUALITY
    Converts GIF -> Video -> Process -> Video output
    Much better quality than direct GIF processing
    """
    from PIL import Image, ImageSequence
    import tempfile
    
    update_status('Processing GIF as VIDEO for MAXIMUM QUALITY...')
    
    try:
        # Create temporary video file
        temp_video = os.path.join(tempfile.gettempdir(), f'temp_gif_{int(time.time())}.mp4')
        
        # Step 1: Convert GIF to video
        update_status('Converting GIF to video...')
        gif = Image.open(target_gif_path)
        
        # Get GIF properties
        width, height = gif.size
        try:
            fps = 1000 / gif.info.get('duration', 100)
            if fps > 50:
                fps = 50
        except:
            fps = 10
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
        
        for frame in ImageSequence.Iterator(gif):
            frame_rgb = frame.convert('RGB')
            frame_array = np.array(frame_rgb)
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            video_writer.write(frame_bgr)
        
        video_writer.release()
        update_status(f'✅ Converted to video at {fps} FPS')
        
        # Step 2: Process video with face swap
        update_status('Processing video with face swap...')
        temp_output_video = output_path.replace('.gif', '.mp4')
        
        # Set temp paths
        old_target = roop.globals.target_path
        old_output = roop.globals.output_path
        
        roop.globals.target_path = temp_video
        roop.globals.output_path = temp_output_video
        
        # Process as video (uses existing video pipeline)
        create_temp(temp_video)
        extract_frames(temp_video, fps)
        temp_frame_paths = get_temp_frame_paths(temp_video)
        
        if temp_frame_paths:
            for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
                update_status('Processing frames...', frame_processor.NAME)
                frame_processor.process_video(source_path, temp_frame_paths)
                frame_processor.post_process()
        
        create_video(temp_video, fps)
        move_temp(temp_video, temp_output_video)
        clean_temp(temp_video)
        
        # Restore paths
        roop.globals.target_path = old_target
        roop.globals.output_path = old_output
        
        update_status('✅ Video processing complete!')
        
        # Step 3: Convert back to GIF (if user wants GIF output)
        if output_path.endswith('.gif'):
            update_status('Converting back to GIF...')
            
            # Read processed video
            cap = cv2.VideoCapture(temp_output_video)
            frames = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_frame = Image.fromarray(frame_rgb)
                frames.append(pil_frame)
            
            cap.release()
            
            # Save as GIF with high quality
            frame_duration = int(1000 / fps)
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0,
                optimize=True,
                quality=95
            )
            
            # Clean up temp video
            try:
                os.remove(temp_output_video)
            except:
                pass
            
            update_status(f'✅ HIGH QUALITY GIF saved! {len(frames)} frames')
        else:
            # Keep as video
            os.rename(temp_output_video, output_path)
            update_status('✅ Saved as high quality video!')
        
        # Clean up
        try:
            os.remove(temp_video)
        except:
            pass
        
    except Exception as e:
        update_status(f'Error in video conversion: {e}')
        raise


def start() -> None:
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
    
    if not roop.globals.output_path:
        update_status('Error: Output path not set.')
        return

    for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    
    # ADDED: Handle GIF processing
    if is_gif(roop.globals.target_path):
        try:
            process_gif(roop.globals.source_path, roop.globals.target_path, roop.globals.output_path)
            
            if os.path.exists(roop.globals.output_path):
                update_status('Processing to GIF succeed! Generating QR Code.')
                if ui:
                    ui.generate_qr_for_output(roop.globals.output_path)
            else:
                update_status('Processing to GIF failed!')
        except Exception as e:
            update_status(f'GIF processing error: {e}')
        return
    
    # Handle image processing
    if has_image_extension(roop.globals.target_path):
        if predict_image(roop.globals.target_path):
            destroy()
        shutil.copy2(roop.globals.target_path, roop.globals.output_path)
        for frame_processor in get_frame_processors_modules(roop.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_image(roop.globals.source_path, roop.globals.output_path, roop.globals.output_path)
            frame_processor.post_process()
        if is_image(roop.globals.output_path):
            update_status('Processing to image succeed! Generating QR Code.')
            if ui:
                ui.generate_qr_for_output(roop.globals.output_path)
        else:
            update_status('Processing to image failed!')
        return
    
    # Handle video processing
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
        update_status('Processing to video succeed! Generating QR Code.')
        if ui:
            ui.generate_qr_for_output(roop.globals.output_path)
    else:
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