import os
import json
import urllib.request
import urllib.error
from app.compressor import image_to_base64

SYSTEM_INSTRUCTION = (
    "You are a Senior UI/UX Designer and Frontend QA Engineer. Your task is to analyze the "
    "provided web page screenshot and identify layout and visual design issues.\n"
    "Look specifically for:\n"
    "1. Overlapping: text overlapping other text/images, or buttons overlapping columns.\n"
    "2. Overflow: content clipped, or sticking out of its container boundaries.\n"
    "3. Broken Layout: buttons wrapped weirdly, columns misaligned, RWD breaks.\n"
    "4. Low Contrast: text color failing basic readability compared to background.\n"
    "5. Text Truncation: text cut off unnaturally, missing ellipsis (...), or cut off mid-word.\n\n"
    "Assess the severity of each issue (critical, warning, info) and suggest a precise CSS fix."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "has_issues": {"type": "BOOLEAN"},
        "issues": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {
                        "type": "STRING", 
                        "description": "Category of issue: 'overlapping', 'overflow', 'broken_layout', 'low_contrast', 'text_truncation', or 'other'"
                    },
                    "severity": {
                        "type": "STRING",
                        "description": "Severity level: 'critical' (breaking use), 'warning' (bad aesthetics), 'info' (minor adjustment)"
                    },
                    "description": {
                        "type": "STRING",
                        "description": "Detailed description of what is visually wrong."
                    },
                    "selector_or_location": {
                        "type": "STRING",
                        "description": "Visual location or estimated CSS selector of the culprit element."
                    },
                    "suggested_fix": {
                        "type": "STRING",
                        "description": "Exact CSS rules or layout changes recommended to fix the issue."
                    }
                },
                "required": ["type", "severity", "description", "suggested_fix"]
            }
        }
    },
    "required": ["has_issues", "issues"]
}

def get_api_key(config=None):
    """Retrieves the Gemini API Key from environment variables or local config."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
        
    if config and "gemini_api_key" in config:
        return config["gemini_api_key"]
        
    return None

def evaluate_layout(image_path, config=None, custom_prompt=None):
    """
    Sends the visual screenshot to Gemini 1.5 Flash using direct REST HTTP call.
    
    Args:
        image_path (str): Path to the optimized screenshot file.
        config (dict): Optional configuration settings.
        custom_prompt (str): Optional prompt override.
        
    Returns:
        dict: Parsed JSON report matching RESPONSE_SCHEMA.
    """
    api_key = get_api_key(config)
    if not api_key:
        raise ValueError(
            "Gemini API key not found. Please set the GEMINI_API_KEY environment variable "
            "or configure it in visual_qa_config.json."
        )
        
    # Get file MIME type based on extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = "image/webp"
    if ext in (".png", ".png"):
        mime_type = "image/png"
    elif ext in (".jpg", ".jpeg"):
        mime_type = "image/jpeg"
        
    base64_data = image_to_base64(image_path)
    
    prompt = custom_prompt or "Analyze this screenshot and report all layout defects. Return response in strict JSON format."
    
    # Construct standard Gemini API payload
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_INSTRUCTION}\n\nTask: {prompt}"},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA
        }
    }
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            
            # Extract content from response structure
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise ValueError("No response generated by Gemini model.")
                
            text_response = candidates[0]["content"]["parts"][0]["text"]
            return json.loads(text_response)
            
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            message = err_json.get("error", {}).get("message", err_msg)
        except Exception:
            message = err_msg
        raise RuntimeError(f"Gemini API HTTP Error ({e.code}): {message}")
    except Exception as e:
        raise RuntimeError(f"Failed to communicate with Gemini API: {e}")
