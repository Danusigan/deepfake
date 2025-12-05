import os
from urllib.parse import quote
import requests
from dotenv import load_dotenv
import qrcode
from PIL import Image

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # keep secret; do not print

BUCKET = 'images'

def upload_file(local_path: str, dest_path: str):
    """Upload file to Supabase Storage (server-side). Returns True on success."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in env")

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY
    }

    # POST multipart/form-data to upload (upsert true to overwrite)
    params = {"upsert": "true"}
    with open(local_path, "rb") as f:
        files = {"file": (os.path.basename(dest_path), f)}
        r = requests.post(f"{SUPABASE_URL}/storage/v1/object/{BUCKET}", headers=headers, params=params, files=files)
    r.raise_for_status()
    return True

def get_public_url(dest_path: str) -> str:
    # Public URL pattern (works if bucket is public)
    encoded = "/".join(quote(p) for p in dest_path.split("/"))
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{encoded}"

def generate_qr(url: str, out_path: str):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    return out_path

if __name__ == "__main__":
    # Example usage: adjust paths/names
    local_image = r'.\output\generated.png'       # path where your code saves the generated image
    dest_name = 'deepfakes/generated.png'         # path in bucket (can include folders)
    qr_local = r'.\output\generated_qr.png'

    os.makedirs(os.path.dirname(local_image), exist_ok=True)
    os.makedirs(os.path.dirname(qr_local), exist_ok=True)

    # 1) upload image
    upload_file(local_image, dest_name)

    # 2) build public URL and create QR code that points to it
    public_url = get_public_url(dest_name)
    print("Public URL (do not print your keys):", public_url)
    generate_qr(public_url, qr_local)

    # Optionally upload the QR image itself:
    upload_file(qr_local, 'qrcodes/generated_qr.png')
    print("QR generated and uploaded.")