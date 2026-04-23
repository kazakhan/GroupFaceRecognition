import base64
import json
import os
import asyncio
import inspect
import requests
import io
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

DEFAULT_MODEL = "qwen3-vl:8b"

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_mime_type(image_path: str) -> str:
    """
    Get MIME type based on file extension.
    """
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')

def get_image_base64_and_mime(image_path: str) -> Tuple[str, str]:
    """
    Encode image to base64 and return with MIME type.
    """
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = get_image_mime_type(image_path)
        return base64_data, mime_type

def get_image_data_uri(image_path: str) -> str:
    """
    Convert image file to data URI for embedding in messages.
    """
    base64_data, mime_type = get_image_base64_and_mime(image_path)
    return f"data:{mime_type};base64,{base64_data}"

def resize_image_if_needed(image_path: str, max_size_mb: float = 5.0) -> Tuple[bytes, str]:
    """
    Resize image if it's too large. Returns (image_bytes, mime_type).
    Tries to use PIL if available, otherwise returns original.
    """
    try:
        from PIL import Image
    except ImportError:
        # PIL not available, return original
        with open(image_path, "rb") as f:
            return f.read(), get_image_mime_type(image_path)

    try:
        with open(image_path, "rb") as f:
            original_bytes = f.read()

        # Check if image is already small enough
        if len(original_bytes) <= max_size_mb * 1024 * 1024:
            return original_bytes, get_image_mime_type(image_path)

        print(f"Image too large ({len(original_bytes)/1024/1024:.1f} MB), resizing...")

        # Open image with PIL
        img = Image.open(image_path)

        # Calculate new dimensions (max 2048 pixels on longest side)
        max_dimension = 2048
        width, height = img.size

        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized from {width}x{height} to {new_width}x{new_height}")

        # Convert to RGB if necessary (strip alpha channel)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        # Save to bytes with quality compression
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        compressed_bytes = output.getvalue()

        print(f"Compressed to {len(compressed_bytes)/1024/1024:.1f} MB")

        return compressed_bytes, 'image/jpeg'

    except Exception as e:
        print(f"Image resize failed: {e}, using original")
        with open(image_path, "rb") as f:
            return f.read(), get_image_mime_type(image_path)

def validate_ollama_vision_payload(payload: dict):
    """
    Validate payload for Ollama native vision API.
    Prevents common mistakes that cause silent failures.
    """
    if "model" not in payload:
        raise ValueError("Missing 'model' in payload")

    if "images" not in payload:
        raise ValueError("Missing 'images' field (required for vision)")

    if not isinstance(payload["images"], list) or not payload["images"]:
        raise ValueError("'images' must be a non-empty list")

    for img in payload["images"]:
        if not isinstance(img, str):
            raise ValueError("Each image must be a base64 string")
        if img.startswith("data:image"):
            raise ValueError("Do NOT include data:image/... prefix - use raw base64 only")
        if len(img) < 1000:
            print(f"Warning: Image base64 string small ({len(img)} chars), may be invalid")

    # Check for forbidden OpenAI fields
    forbidden = {"messages", "image_url", "content"}
    bad = forbidden.intersection(payload.keys())
    if bad:
        raise ValueError(f"Forbidden OpenAI fields for Ollama vision: {bad}")

def describe_with_direct_ollama(
    image_path: str,
    identification_result: Dict[str, Any],
    model: str = DEFAULT_MODEL,
    base_url: str = "http://192.168.178.33:11434"
) -> str:
    """
    Use Ollama native vision API (/api/generate).
    """
    try:
        if not os.path.exists(image_path):
            return f"Error: Image file not found: {image_path}"
        
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        face_count = identification_result.get("face_count", 0)
        identification_text = json.dumps(identification_result, indent=2)
        
        prompt = (
            "You are a helpful vision assistant that describes images.\n"
            "You will be given a list of people identified in the image.\n"
            "Use exactly those names. Do not guess identities.\n\n"
			"Context: Jamie is the father of Jordan, Amaya, Imola and Jalea. Sarah is the mother of Jordan and Amaya. Dash and Vaughn are friends of Jordan."
            f"Faces detected: {face_count}\n"
            f"Identified people:\n{identification_text}\n\n"
            "Describe the image in natural language."
        )
        
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 500
            }
        }
        
        api_url = f"{base_url.rstrip('/')}/api/generate"
        
        print(f"Calling Ollama API: {api_url}")
        print(f"Image size: {len(image_bytes)} bytes, Base64: {len(image_base64)} chars")
        
        response = requests.post(
            api_url,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        # Debug raw response
        raw_response = response.text
        print(f"Response status: {response.status_code}")
        print(f"Raw response (first 500 chars): {raw_response[:500]}")
        
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {raw_response}")
            return f"JSON decode error: {e}"
        
        print(f"Response keys: {list(result.keys())}")
        
        if "error" in result:
            print(f"API error: {result['error']}")
            return f"API error: {result['error']}"
        
        # Try multiple possible response fields
        response_text = ""
        for field in ["response", "text", "content", "message", "output"]:
            if field in result:
                value = result[field]
                if isinstance(value, str):
                    response_text = value
                    print(f"Found response in field '{field}': length {len(response_text)}")
                    break
                elif isinstance(value, dict):
                    # Try nested fields
                    for subfield in ["content", "text", "response"]:
                        if subfield in value and isinstance(value[subfield], str):
                            response_text = value[subfield]
                            print(f"Found response in {field}.{subfield}: length {len(response_text)}")
                            break
        
        print(f"Final response length: {len(response_text)} chars")
        
        if response_text:
            print(f"Response preview: {response_text[:200]}...")
        else:
            print("WARNING: Empty response from model")
            print(f"Full result: {result}")
        
        return response_text
        
    except Exception as e:
        error_msg = f"Ollama vision error: {e}"
        print(error_msg)
        return error_msg

def describe_image_with_identification(
        image_path: str,
        identification_result: Dict[str, Any],
        model: str = DEFAULT_MODEL,
        client: Optional[Any] = None,
        base_url: str = "http://192.168.178.33:11434"
) -> str:
    """
    Main function to generate image description.
    Uses Ollama native vision API (the only reliable way with Ollama).

    Args:
        image_path: Path to the image.
        identification_result: Output from identify_people_in_image_tool.
        model: Ollama model name (default: "qwen3-vl:8b").
        client: Optional pre‑configured client (ignored for vision, kept for compatibility).
        base_url: Ollama API base URL (without /v1 for native API).

    Returns:
        Natural‑language description string.
    """
    # Use Ollama native vision API directly (autogen doesn't work for vision with Ollama)
    return describe_with_direct_ollama(image_path, identification_result, model, base_url)

def get_vision_model_client(base_url: str = "http://192.168.178.33:11434", model: str = DEFAULT_MODEL):
    """
    Compatibility function - tries to create appropriate autogen client.
    Returns None if direct Ollama API should be used.
    """
    try:
        # Try OpenAIChatCompletionClient first (most reliable)
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            return OpenAIChatCompletionClient(
                model=model,
                api_key="NotRequiredSinceWeAreLocal",
                base_url=base_url,
                model_capabilities={
                    "json_output": False,
                    "vision": True,
                    "function_calling": True,
                    "structured_output": False,
                },
            )
        except ImportError:
            try:
                from autogen import OpenAIChatCompletionClient
                return OpenAIChatCompletionClient(
                    model=model,
                    api_key="NotRequiredSinceWeAreLocal",
                    base_url=base_url,
                    model_capabilities={
                        "json_output": False,
                        "vision": True,
                        "function_calling": True,
                        "structured_output": False,
                    },
                )
            except ImportError:
                # No autogen client available
                return None
    except Exception:
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Create a mock identification result for testing
        mock_ident = {
            "people": [
                {"name": "Alice", "confidence": 0.85},
                {"name": "Unknown", "confidence": 0.42}
            ],
            "face_count": 2
        }

        img_path = sys.argv[1]
        if os.path.exists(img_path):
            desc = describe_image_with_identification(img_path, mock_ident)
            print("Description:", desc)
        else:
            print(f"Image file not found: {img_path}")
    else:
        print("Usage: python vision_client.py <image_path>")