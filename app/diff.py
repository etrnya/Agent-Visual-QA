import os
from PIL import Image, ImageChops

def compare_images(image_path_a, image_path_b, diff_output_path=None, threshold_percent=0.1, tolerance=15):
    """
    Compares two images and calculates the percentage of visual difference.
    Pads the images if their sizes do not match.
    
    Args:
        image_path_a (str): Path to first image (e.g. baseline).
        image_path_b (str): Path to second image (e.g. current render).
        diff_output_path (str): Optional path to save a visual diff highlight image.
        threshold_percent (float): Maximum allowed difference percentage to consider similar.
        tolerance (int): Intensity tolerance (0-255) to ignore anti-aliasing/rendering noise.
        
    Returns:
        tuple: (diff_percent, is_similar)
            diff_percent (float): Percent of pixels that changed (0.0 to 100.0).
            is_similar (bool): True if diff_percent <= threshold_percent.
    """
    if not os.path.exists(image_path_a) or not os.path.exists(image_path_b):
        raise FileNotFoundError("One or both input image files do not exist.")
        
    with Image.open(image_path_a) as img_a_file, Image.open(image_path_b) as img_b_file:
        img_a = img_a_file.convert("RGB")
        img_b = img_b_file.convert("RGB")
        
        # Determine max bounding box to pad images if heights/widths differ
        width = max(img_a.width, img_b.width)
        height = max(img_a.height, img_b.height)
        
        if img_a.size != (width, height):
            new_a = Image.new("RGB", (width, height), (255, 255, 255))
            new_a.paste(img_a, (0, 0))
            img_a = new_a
            
        if img_b.size != (width, height):
            new_b = Image.new("RGB", (width, height), (255, 255, 255))
            new_b.paste(img_b, (0, 0))
            img_b = new_b
            
        # Compute absolute pixel difference
        with ImageChops.difference(img_a, img_b) as diff:
            # Convert difference to grayscale to simplify thresholding
            with diff.convert("L") as diff_gray:
                if hasattr(diff_gray, "get_flattened_data"):
                    pixels = diff_gray.get_flattened_data()
                else:
                    pixels = diff_gray.getdata()
                
                # Count pixels that differ by more than the tolerance value
                changed_pixels = sum(1 for p in pixels if p > tolerance)
                total_pixels = width * height
                
                diff_percent = (changed_pixels / total_pixels) * 100.0
                is_similar = diff_percent <= threshold_percent
                
                # Save diff visualization highlight if requested
                if diff_output_path:
                    os.makedirs(os.path.dirname(os.path.abspath(diff_output_path)), exist_ok=True)
                    # Red overlay mask where difference exceeds tolerance
                    with Image.new("RGB", (width, height), (255, 0, 0)) as highlight:
                        with diff_gray.point(lambda p: 255 if p > tolerance else 0) as mask:
                            # Blend: original baseline image, red highlight, masked by pixel changes
                            with Image.composite(highlight, img_a, mask) as diff_img:
                                diff_img.save(diff_output_path)
                                
    return diff_percent, is_similar

