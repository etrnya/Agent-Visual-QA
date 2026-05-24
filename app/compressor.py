import os
import io
import base64
from PIL import Image

def compress_and_resize(image_path, output_path=None, max_width=1024, quality=80, format="WEBP"):
    """
    Resizes an image to a maximum width while preserving aspect ratio, 
    and compresses it to WebP or JPEG.
    
    Args:
        image_path (str): Path to original image.
        output_path (str): Path to save the compressed image. If None, returns bytes.
        max_width (int): Target maximum width. Downscales if original is wider.
        quality (int): Compression quality (1-100).
        format (str): Target format ("WEBP" or "JPEG").
        
    Returns:
        str or bytes: Output path if output_path is specified, else raw compressed bytes.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")
        
    with Image.open(image_path) as img:
        work_img = img
        background = None
        
        # Preserving transparency if converting to WebP, or converting to RGB if JPEG
        if format.upper() == "JPEG" and img.mode in ("RGBA", "LA"):
            # Create white background for transparent pixels
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == "RGBA" else img.split()[1])
            work_img = background
        elif img.mode not in ("RGB", "RGBA"):
            work_img = img.convert("RGB")
            
        # Resize if wider than max_width
        resized_img = None
        if work_img.width > max_width:
            scale = max_width / float(work_img.width)
            new_height = int(float(work_img.height) * scale)
            resized_img = work_img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            work_img = resized_img
            
        try:
            if output_path:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                work_img.save(output_path, format=format, quality=quality)
                return os.path.abspath(output_path)
            else:
                buffer = io.BytesIO()
                work_img.save(buffer, format=format, quality=quality)
                return buffer.getvalue()
        finally:
            if resized_img:
                resized_img.close()
            if background:
                background.close()
            if work_img is not img and work_img is not resized_img and work_img is not background:
                work_img.close()

def crop_roi(image_path, box, output_path=None):
    """
    Crops a Region of Interest (ROI) out of the image.
    
    Args:
        image_path (str): Path to original image.
        box (tuple): Coordinates of the crop box (left, top, right, bottom).
        output_path (str): Path to save the cropped crop. If None, returns bytes.
        
    Returns:
        str or bytes: Output path if specified, else raw cropped PNG bytes.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")
        
    with Image.open(image_path) as img:
        with img.crop(box) as cropped:
            if output_path:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                cropped.save(output_path, format="PNG")
                return os.path.abspath(output_path)
            else:
                buffer = io.BytesIO()
                cropped.save(buffer, format="PNG")
                return buffer.getvalue()

def image_to_base64(image_bytes_or_path):
    """
    Converts raw image bytes or an image file to a base64 encoded string.
    
    Args:
        image_bytes_or_path (bytes or str): Binary image data or image file path.
        
    Returns:
        str: Base64 encoded representation of the image.
    """
    if isinstance(image_bytes_or_path, bytes):
        data = image_bytes_or_path
    else:
        if not os.path.exists(image_bytes_or_path):
            raise FileNotFoundError(f"File not found: {image_bytes_or_path}")
        with open(image_bytes_or_path, "rb") as f:
            data = f.read()
            
    return base64.b64encode(data).decode("utf-8")
