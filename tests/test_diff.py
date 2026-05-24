import os
import unittest
import shutil
from PIL import Image
from app.diff import compare_images

class TestDiff(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_dir = os.path.join(self.base_dir, ".visual_qa_test_output_diff")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create baseline image (100x100 blue square)
        self.img_a_path = os.path.join(self.test_dir, "img_a.png")
        img_a = Image.new("RGB", (100, 100), (0, 0, 255))
        img_a.save(self.img_a_path)
        
        # Create identical image
        self.img_b_path = os.path.join(self.test_dir, "img_b.png")
        img_b = Image.new("RGB", (100, 100), (0, 0, 255))
        img_b.save(self.img_b_path)
        
        # Create completely different image (100x100 red square)
        self.img_c_path = os.path.join(self.test_dir, "img_c.png")
        img_c = Image.new("RGB", (100, 100), (255, 0, 0))
        img_c.save(self.img_c_path)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_compare_identical(self):
        diff_pct, similar = compare_images(self.img_a_path, self.img_b_path, threshold_percent=0.1)
        self.assertEqual(diff_pct, 0.0)
        self.assertTrue(similar)
        
    def test_compare_different(self):
        diff_path = os.path.join(self.test_dir, "diff_highlight.png")
        diff_pct, similar = compare_images(self.img_a_path, self.img_c_path, diff_output_path=diff_path, threshold_percent=0.1)
        
        self.assertEqual(diff_pct, 100.0)  # 100% of pixels changed
        self.assertFalse(similar)
        self.assertTrue(os.path.exists(diff_path))

if __name__ == "__main__":
    unittest.main()
