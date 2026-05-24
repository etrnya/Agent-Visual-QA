import os
import unittest
import shutil
from app.browser import capture_screenshots

class TestBrowser(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fixture_path = os.path.join(self.base_dir, "tests", "fixtures", "test.html")
        self.output_dir = os.path.join(self.base_dir, ".visual_qa_test_output_browser")
        
    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_capture_screenshots(self):
        viewports = {
            "mobile": {"width": 375, "height": 812}
        }
        res = capture_screenshots(self.fixture_path, self.output_dir, viewports=viewports, full_page=False)
        self.assertIn("mobile", res)
        
        saved_file = res["mobile"]
        self.assertTrue(os.path.exists(saved_file))
        self.assertTrue(saved_file.endswith(".png"))
        self.assertTrue(os.path.getsize(saved_file) > 0)

if __name__ == "__main__":
    unittest.main()
