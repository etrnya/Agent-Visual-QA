import os
import unittest
import shutil
from PIL import Image
from app.compressor import compress_and_resize, crop_roi, image_to_base64

class TestCompressor(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_dir = os.path.join(self.base_dir, ".visual_qa_test_output_compressor")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a mock raw high-res image (2000x1000)
        self.mock_image_path = os.path.join(self.test_dir, "mock_raw.png")
        with Image.new("RGBA", (2000, 1000), (0, 128, 255, 255)) as img:
            img.save(self.mock_image_path)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_compress_and_resize(self):
        output_webp = os.path.join(self.test_dir, "compressed.webp")
        # Resize to max_width 800px (from 2000px)
        compress_and_resize(self.mock_image_path, output_webp, max_width=800, quality=75, format="WEBP")
        
        self.assertTrue(os.path.exists(output_webp))
        with Image.open(output_webp) as img:
            self.assertEqual(img.width, 800)
            self.assertEqual(img.height, 400)  # Aspect ratio preserved (2:1)
            self.assertEqual(img.format, "WEBP")
        
    def test_crop_roi(self):
        output_crop = os.path.join(self.test_dir, "cropped.png")
        box = (50, 50, 150, 150)
        crop_roi(self.mock_image_path, box, output_crop)
        
        self.assertTrue(os.path.exists(output_crop))
        with Image.open(output_crop) as img:
            self.assertEqual(img.size, (100, 100))
            self.assertEqual(img.format, "PNG")
        
    def test_image_to_base64(self):
        b64 = image_to_base64(self.mock_image_path)
        self.assertTrue(isinstance(b64, str))
        self.assertTrue(len(b64) > 0)

if __name__ == "__main__":
    unittest.main()
