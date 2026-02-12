import os
import re
import json
import yaml

def load_config(config_path='config.yaml') -> dict:
    """Loads configuration from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing config file: {exc}")

def ensure_dir_exists(path: str) -> None:
    """Creates a directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def sanitize_filename(name: str) -> str:
    """Sanitizes a string to be safe for filenames.

    Converts to lowercase and replaces spaces with underscores
    to match Obsidian vault naming convention.
    """
    name = name.lower().strip()
    name = re.sub(r'[\\/*?":"<>|]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def extract_json_from_text(text: str) -> dict:
    """Extracts JSON object from a text string (e.g., from LLM response)."""
    # Try to find JSON block enclosed in ```json ... ```
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Try to find just a JSON object {*}
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            raise ValueError("No JSON found in text")
            
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON content: {e}")

