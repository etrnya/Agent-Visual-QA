import os
import time
from playwright.sync_api import sync_playwright

def capture_screenshots(url_or_path, output_dir, viewports=None, full_page=True, wait_ms=1000):
    """
    Launches headless browser and captures screenshots for given viewports.
    
    Args:
        url_or_path (str): HTTP/HTTPS URL or local HTML file path.
        output_dir (str): Directory where screenshots will be saved.
        viewports (dict): Dict of name -> {"width": W, "height": H}.
        full_page (bool): True to take screenshot of the entire scrollable page.
        wait_ms (int): Additional wait duration in milliseconds before screenshotting.
        
    Returns:
        dict: Mapping of viewport name to absolute screenshot file path.
    """
    if viewports is None:
        viewports = {
            "mobile": {"width": 375, "height": 812},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1920, "height": 1080}
        }
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Handle local file path formatting for Chromium
    if not (url_or_path.startswith("http://") or url_or_path.startswith("https://")):
        abs_path = os.path.abspath(url_or_path)
        if os.path.exists(abs_path):
            url_or_path = f"file:///{abs_path.replace(os.sep, '/')}"
            
    screenshot_paths = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for name, size in viewports.items():
            width = size.get("width", 1280)
            height = size.get("height", 720)
            
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1
            )
            
            page = context.new_page()
            
            try:
                page.goto(url_or_path, wait_until="networkidle")
            except Exception:
                # Fallback if networkidle times out
                page.goto(url_or_path)
                
            if wait_ms > 0:
                page.wait_for_timeout(wait_ms)
                
            filename = f"screenshot_{name}.png"
            path = os.path.join(output_dir, filename)
            page.screenshot(path=path, full_page=full_page)
            screenshot_paths[name] = os.path.abspath(path)
            
            context.close()
            
        browser.close()
        
    return screenshot_paths

def capture_element_screenshot(url_or_path, selector, output_path, viewport=None, wait_ms=1000):
    """
    Navigates to URL, locates a DOM selector, and captures a screenshot of just that element.
    
    Args:
        url_or_path (str): HTTP/HTTPS URL or local HTML file path.
        selector (str): CSS selector of the DOM element to capture.
        output_path (str): Target output file path (.png).
        viewport (dict): Optional custom viewport {"width": W, "height": H}.
        wait_ms (int): Additional wait duration in milliseconds before screenshotting.
        
    Returns:
        str: Absolute file path of the saved element screenshot.
    """
    if viewport is None:
        viewport = {"width": 1280, "height": 720}
        
    if not (url_or_path.startswith("http://") or url_or_path.startswith("https://")):
        abs_path = os.path.abspath(url_or_path)
        if os.path.exists(abs_path):
            url_or_path = f"file:///{abs_path.replace(os.sep, '/')}"
            
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            page.goto(url_or_path, wait_until="networkidle")
        except Exception:
            page.goto(url_or_path)
            
        if wait_ms > 0:
            page.wait_for_timeout(wait_ms)
            
        element = page.locator(selector)
        element.scroll_into_view_if_needed()
        element.screenshot(path=output_path)
        
        context.close()
        browser.close()
        
    return os.path.abspath(output_path)
