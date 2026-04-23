import json
from typing import Dict, Any
from face_recognition_tool import identify_people_in_image

def identify_people_in_image_tool(image_path: str) -> Dict[str, Any]:
    """
    Detect faces in an image and match against known face encodings.
    
    This tool is the source of truth for person identification.
    The LLM must consume its output and never infer or guess identities.
    
    Args:
        image_path: Path to the image file.
    
    Returns:
        JSON string containing people list and face count.
        Example:
        {
            "people": [
                {"name": "Alice", "confidence": 0.87},
                {"name": "Unknown", "confidence": 0.42}
            ],
            "face_count": 2
        }
    """
    result = identify_people_in_image(image_path)
    return result

def get_tool_schema() -> Dict[str, Any]:
    """
    Return the function schema for registration with pyautogen.
    """
    return {
        "type": "function",
        "function": {
            "name": "identify_people_in_image",
            "description": "Detect faces in an image and match against known face encodings. Returns structured identification results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file."
                    }
                },
                "required": ["image_path"],
                "additionalProperties": False
            }
        }
    }

if __name__ == "__main__":
    # Test the tool
    import sys
    if len(sys.argv) > 1:
        result = identify_people_in_image_tool(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python tools.py <image_path>")