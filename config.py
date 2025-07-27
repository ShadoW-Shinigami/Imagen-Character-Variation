"""Configuration settings for the Character Creation System"""

import zipfile
from typing import Dict, List, Any
from dataclasses import dataclass

# Character configuration options
CHARACTER_ETHNICITIES = ["Asian", "Caucasian", "African", "Hispanic", "Middle Eastern", "Native American", "Mixed"]
CHARACTER_GENDERS = ["Male", "Female", "Non-binary"]
HAIR_COLORS = ["Black", "Brown", "Blonde", "Red", "Gray", "White", "Auburn", "Strawberry Blonde"]
EYE_COLORS = ["Brown", "Blue", "Green", "Hazel", "Gray", "Amber"]
BUILD_TYPES = ["Slim", "Athletic", "Average", "Muscular", "Curvy", "Heavy"]
HEIGHT_TYPES = ["Short", "Average", "Tall"]

# Age ranges for dropdown
AGE_RANGES = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]

# Clothing options
CLOTHING_STYLES = [
    "Casual jeans and t-shirt",
    "Business casual",
    "Formal suit",
    "Sporty workout attire",
    "Elegant dress",
    "Bohemian style",
    "Vintage clothing",
    "Modern streetwear"
]

# API Configuration
@dataclass
class APIConfig:
    """API configuration settings"""
    imagen4_params: Dict[str, Any]
    kontext_max_params: Dict[str, Any]
    kontext_lora_params: Dict[str, Any]

# Default API parameters
DEFAULT_API_CONFIG = APIConfig(
    imagen4_params={
        "aspect_ratio": "1:1",
        "num_images": 1,
        "negative_prompt": "",
        "seed": 69420
    },
    kontext_max_params={
        "guidance_scale": 3.5,
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "2",
        "aspect_ratio": "1:1",
        "seed": 69420
    },
    kontext_lora_params={
        "num_inference_steps": 30,
        "guidance_scale": 2.5,
        "num_images": 1,
        "output_format": "png",
        "resolution_mode": "match_input",
        "acceleration": "none"
    }
)

# Style configurations
STYLE_CONFIGS = {
    "ghibli": {
        "name": "Studio Ghibli",
        "lora_path": "https://huggingface.co/Owen777/Kontext-Style-Loras/resolve/main/Ghibli_lora_weights.safetensors",
        "prompt_template": "Turn this image into the Ghibli style.",
        "weight": 1,
        "description": "Magical, whimsical animation style from Studio Ghibli films"
    },
    "rick_morty": {
        "name": "Rick & Morty",
        "lora_path": "https://huggingface.co/Owen777/Kontext-Style-Loras/resolve/main/Rick_Morty_lora_weights.safetensors",
        "prompt_template": "Turn this image into the Rick Morty style.",
        "weight": 1,
        "description": "Distinctive cartoon style from the Rick and Morty TV series"
    }
}

# Default consistency test prompts
DEFAULT_TEST_PROMPTS = [
    "Character sitting on a chair, same appearance",
    "Character walking forward, confident pose",
    "Character waving hello, friendly expression",
    "Character in a thinking pose, hand on chin",
    "Character with arms crossed, serious expression",
    "Character smiling warmly, happy expression",
    "Character with surprised expression, eyes wide",
    "Character looking thoughtful and contemplative",
    "Character laughing heartily, joyful mood",
    "Character with determined expression, focused",
    "Character wearing casual jeans and t-shirt",
    "Character in formal business attire",
    "Character wearing workout clothes at gym",
    "Character in winter coat and scarf",
    "Character in elegant evening wear",
    "Character in a modern office environment",
    "Character outdoors in a park setting",
    "Character in a cozy home kitchen",
    "Character at a beach during sunset",
    "Character in a library or bookstore",
    "Character cooking in the kitchen",
    "Character reading a book intently",
    "Character using a smartphone",
    "Character exercising or stretching",
    "Character painting or drawing",
    "Character portrait, close-up face shot",
    "Character from side profile view",
    "Character from behind, looking over shoulder",
    "Character full body from slight distance",
    "Character in three-quarter view angle"
]

# UI Configuration
UI_CONFIG = {
    "title": "🎨 AI Character Creation Studio",
    "description": "Create consistent character images using Imagen 4, Kontext Max, and style LoRAs",
    "theme_colors": {
        "primary": "#2E8B57",  # Sea green
        "secondary": "#4682B4",  # Steel blue
        "accent": "#20B2AA"     # Light sea green
    },
    "gallery_columns": 4,
    "max_batch_size": 10
}

# Debug and Performance Configuration
DEBUG_CONFIG = {
    "default_debug_mode": False,
    "log_api_requests": True,
    "log_api_responses": True,
    "show_timing_info": True,
    "detailed_error_messages": True
}

# Timeout Configuration (in seconds)
TIMEOUT_CONFIG = {
    "imagen4_timeout": 120,      # 2 minutes for base character generation
    "kontext_max_timeout": 300,  # 5 minutes per variation
    "kontext_lora_timeout": 240, # 4 minutes per style transfer
    "download_timeout": 60,      # 1 minute for image downloads
    "total_session_timeout": 36000 # 10 hours for entire session
}

# Character Management Configuration
CHARACTER_MANAGEMENT_CONFIG = {
    "cache_duration_seconds": 30,  # How long to cache character discovery results
    "max_preview_images": 6,       # Maximum preview images per character
    "thumbnail_size": (200, 200),  # Thumbnail dimensions for preview
    "supported_image_formats": [".png", ".jpg", ".jpeg"],
    "metadata_files": [
        "base_character_metadata.json",
        "base_image_metadata.json"
    ],
    "directory_patterns": {
        "session": "Session_*",
        "character": "Char_*",
        "consistency": "ConsistencyTests",
        "styles": "Styles"
    }
}

# ZIP Export Configuration  
ZIP_EXPORT_CONFIG = {
    "compression_level": zipfile.ZIP_DEFLATED,
    "include_metadata_by_default": True,
    "estimated_compression_ratio": 0.7,  # 70% of original size
    "temp_file_cleanup": True,
    "readme_template": "character_export_readme.txt",
    "batch_size_warning_mb": 100,  # Warn if batch ZIP exceeds this size
    "max_characters_per_batch": 50
}

# Library Display Configuration
LIBRARY_DISPLAY_CONFIG = {
    "characters_per_page": 20,
    "gallery_columns": 3,
    "preview_image_size": (300, 300),
    "show_creation_date": True,
    "show_image_counts": True,
    "auto_refresh_interval": None,  # Set to seconds for auto-refresh, None to disable
    "sort_options": ["date_desc", "date_asc", "name_asc", "image_count_desc"]
}