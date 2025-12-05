import os
import traceback

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def save_bytes(path: str, data: bytes):
    ensure_dir(path)
    try:
        with open(path, 'wb') as f:
            f.write(data)
    except Exception:
        print("Failed to save bytes:", path)
        traceback.print_exc()
        raise

def save_pil_image(path: str, pil_image):
    ensure_dir(path)
    try:
        pil_image.save(path)
    except Exception:
        print("Failed to save PIL image:", path)
        traceback.print_exc()
        raise

def save_cv2_image(path: str, img):
    # img expected as numpy array in RGB or BGR uint8. Convert RGB->BGR for cv2 if needed.
    import cv2
    import numpy as np
    ensure_dir(path)
    try:
        if img.dtype != np.uint8:
            img = (img * 255).astype('uint8')
        # If image has 3 channels and looks RGB, convert to BGR:
        if img.ndim == 3 and img.shape[2] == 3:
            img_to_write = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img_to_write = img
        ok = cv2.imwrite(path, img_to_write)
        if not ok:
            raise RuntimeError("cv2.imwrite returned False")
    except Exception:
        print("Failed to save cv2 image:", path)
        traceback.print_exc()
        raise