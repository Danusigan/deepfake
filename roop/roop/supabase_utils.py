import io
import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import qrcode
from PIL import Image
from urllib.parse import quote

# lazy import for supabase client creation
from supabase import create_client

load_dotenv()

def _get_env():
    return (
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY"),
        os.environ.get("SUPABASE_BUCKET", "images"),
    )

def _create_client():
    url, key, _ = _get_env()
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in the environment to use Supabase upload functions"
        )
    return create_client(url, key)

def upload_image_and_generate_qr(image_bytes: bytes, image_name: str) -> Dict[str, str]:
    """
    Upload image_bytes to Supabase storage, create public URL, generate QR PNG
    that points to the public URL, upload QR and return both URLs.
    """
    url, key, bucket = _get_env()
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in the environment to use Supabase upload functions"
        )

    supabase = _create_client()

    # Generate unique filename to avoid conflicts
    import time
    timestamp = int(time.time() * 1000)
    image_filename = f"{timestamp}_{image_name}"
    image_path = f"generated/{image_filename}"

    # Upload image with proper error handling
    print(f"[SUPABASE] Uploading image to {bucket}/{image_path}...")
    try:
        upload_resp = supabase.storage.from_(bucket).upload(
            image_path, 
            image_bytes,
            {"content-type": "image/png"}
        )
        print(f"[SUPABASE] Upload response: {upload_resp}")
    except Exception as e:
        print(f"[SUPABASE] Image upload error: {e}")
        raise RuntimeError(f"Image upload failed: {e}")

    # Construct the FULL Supabase URL (NOT shortened)
    encoded_path = "/".join(quote(p, safe='') for p in image_path.split('/'))
    public = f"{url}/storage/v1/object/public/{bucket}/{encoded_path}"
    print(f"[SUPABASE] Image public URL: {public}")
    print(f"[SUPABASE] Full URL length: {len(public)} characters")

    # Generate QR code with FULL Supabase URL
    print(f"[SUPABASE] Generating QR code with URL: {public}")
    qr = qrcode.QRCode(
        version=None,  # Auto-detect version based on data length
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(public)  # Add the FULL Supabase URL
    qr.make(fit=True)
    print(f"[SUPABASE] QR version: {qr.version}, Box size: {qr.box_size}")
    
    qr_img: Image.Image = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_bytes = qr_buf.getvalue()
    print(f"[SUPABASE] QR code generated (size: {len(qr_bytes)} bytes)")

    # Upload QR code
    qr_filename = f"{timestamp}_{image_name.replace('.png', '_qr.png')}"
    qr_path = f"qrcodes/{qr_filename}"
    
    print(f"[SUPABASE] Uploading QR code to {bucket}/{qr_path}...")
    try:
        qr_resp = supabase.storage.from_(bucket).upload(
            qr_path, 
            qr_bytes,
            {"content-type": "image/png"}
        )
        print(f"[SUPABASE] QR uploaded successfully")
    except Exception as e:
        print(f"[SUPABASE] QR upload error: {e}")
        raise RuntimeError(f"QR upload failed: {e}")

    # Get QR public URL
    encoded_qr_path = "/".join(quote(p, safe='') for p in qr_path.split('/'))
    qr_public = f"{url}/storage/v1/object/public/{bucket}/{encoded_qr_path}"
    print(f"[SUPABASE] QR public URL: {qr_public}")

    # Insert metadata into database
    try:
        supabase.table("generated_images").insert({
            "name": image_filename, 
            "url": public, 
            "qr_url": qr_public,
            "created_at": "now()"
        }).execute()
        print(f"[SUPABASE] Metadata inserted into DB")
    except Exception as e:
        print(f"[SUPABASE] DB insert skipped: {e}")

    return {
        "url": public, 
        "qr_url": qr_public,
        "image_path": image_path,
        "qr_path": qr_path
    }

def test_upload_local_file(local_path: str):
    """Quick debug: upload a local file and print result."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)
    with open(local_path, "rb") as f:
        data = f.read()
    return upload_image_and_generate_qr(data, os.path.basename(local_path))