import qrcode
from PIL import Image, ImageOps
import customtkinter as ctk
from typing import Tuple

def generate_qr_code(data: str, size: Tuple[int, int]) -> ctk.CTkImage:
    """
    Generates a QR code image from input data.
    
    In a real-world scenario, 'data' would be the public URL of the uploaded output file.
    The QR code will contain this URL, allowing users to scan and access the content.
    """
    # Generate the QR code as a PIL Image object
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Make image with colors that fit the dark theme
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # Resize the image to fit the required size
    img_resized = ImageOps.fit(img, size, Image.LANCZOS)
    
    # Convert to CTkImage for display in the CustomTkinter GUI
    return ctk.CTkImage(img_resized, size=img_resized.size)