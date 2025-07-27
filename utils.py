"""Utility functions for the Character Creation System"""

import os
import requests
import base64
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
from io import BytesIO
import fal_client

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    # dotenv not installed, skip loading
    pass

def create_session_folder(session_id: str, character_id: str) -> Tuple[Path, Path]:
    """Create organized folder structure for session outputs"""
    base_path = Path(session_id) / character_id
    consistency_path = base_path / "ConsistencyTests"
    styles_path = base_path / "Styles"
    
    # Create directories
    base_path.mkdir(parents=True, exist_ok=True)
    consistency_path.mkdir(parents=True, exist_ok=True)
    styles_path.mkdir(parents=True, exist_ok=True)
    
    return base_path, consistency_path

def build_character_prompt(config: Dict[str, Any]) -> str:
    """Build comprehensive character generation prompt"""
    prompt_parts = [
        f"Professional photograph of a {config.get('age', '25')}-year-old {config.get('ethnicity', 'person')} {config.get('gender', '').lower()}",
        f"with {config.get('hair_color', 'brown').lower()} hair and {config.get('eye_color', 'brown').lower()} eyes",
        f"{config.get('build', 'average').lower()} build, {config.get('height', 'average').lower()} height",
        f"wearing {config.get('clothing', 'casual clothing')}"
    ]
    
    # Add facial features if specified
    if config.get('facial_features'):
        prompt_parts.append(f"with {config['facial_features']}")
    
    # Photography requirements
    prompt_parts.extend([
        "full body image",
        "plain white background",
        "professional studio lighting",
        "high quality",
        "detailed",
        "realistic"
    ])
    
    return ", ".join(prompt_parts)

def save_image_from_url(url: str, filepath: Path, max_retries: int = 3) -> bool:
    """Download and save image from URL with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to save {filepath} after {max_retries} attempts: {e}")
                return False
            time.sleep(1)  # Wait before retry
    
    return False

def convert_image_to_base64(image_path: Path) -> Optional[str]:
    """Convert image file to base64 string"""
    try:
        with open(image_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_string
    except Exception as e:
        print(f"Failed to convert {image_path} to base64: {e}")
        return None

def convert_image_to_data_url(image_path: Path) -> Optional[str]:
    """Convert image file to base64 data URL for API usage"""
    try:
        with open(image_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{base64_string}"
    except Exception as e:
        print(f"Failed to convert {image_path} to data URL: {e}")
        return None

def create_metadata_entry(prompt: str, params: Dict[str, Any], result: Dict[str, Any], 
                         image_path: Optional[Path] = None) -> Dict[str, Any]:
    """Create metadata entry for generated image"""
    return {
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "parameters": params,
        "result": result,
        "image_path": str(image_path) if image_path else None,
        "success": image_path.exists() if image_path else False
    }

def save_metadata(metadata: Dict[str, Any], filepath: Path) -> None:
    """Save metadata to JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Failed to save metadata to {filepath}: {e}")

def validate_api_key() -> Tuple[bool, str]:
    """Validate FAL API key and return status message with setup guidance"""
    try:
        if 'FAL_KEY' not in os.environ:
            env_file_exists = Path('.env').exists()
            env_example_exists = Path('.env.example').exists()
            
            error_msg = "❌ FAL API key not found.\n\n"
            
            if env_example_exists and not env_file_exists:
                error_msg += "Setup instructions:\n"
                error_msg += "1. Copy .env.example to .env\n"
                error_msg += "2. Edit .env and add your FAL API key\n"
                error_msg += "3. Get your API key from: https://fal.ai/dashboard\n\n"
            elif env_file_exists:
                error_msg += "Found .env file but FAL_KEY is not set.\n"
                error_msg += "Please add: FAL_KEY=your_api_key_here to your .env file\n\n"
            else:
                error_msg += "Alternative setup methods:\n"
                error_msg += "• Create .env file with: FAL_KEY=your_api_key_here\n"
                error_msg += "• Or set environment variable: export FAL_KEY=your_api_key_here\n\n"
            
            error_msg += "Get your API key from: https://fal.ai/dashboard"
            return False, error_msg
        
        key = os.environ['FAL_KEY']
        if len(key) < 10:
            return False, "❌ Invalid API key format. Please check your FAL_KEY value."
        
        if key == "your_fal_api_key_here" or key == "your_api_key_here":
            return False, "❌ Please replace the placeholder with your actual FAL API key.\nGet your key from: https://fal.ai/dashboard"
        
        return True, "✅ API key validated successfully!"
    except Exception as e:
        return False, f"❌ API validation failed: {str(e)}"

def resize_image_for_display(image_path: Path, max_size: int = 512) -> Optional[Image.Image]:
    """Resize image for display in Gradio while maintaining aspect ratio"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            return img.copy()
    except Exception as e:
        print(f"Failed to resize image {image_path}: {e}")
        return None

def get_image_dimensions(image_path: Path) -> Tuple[int, int]:
    """Get image dimensions"""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (0, 0)

class APIWrapper:
    """Wrapper class for FAL API calls with enhanced status tracking"""
    
    def __init__(self, debug_mode: bool = False):
        self.client = fal_client
        self.debug_mode = debug_mode
        self.current_status = ""
    
    def _log_status(self, message: str, level: str = "info"):
        """Log status message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        if level == "debug" and not self.debug_mode:
            return formatted_msg
        
        print(formatted_msg)
        self.current_status = formatted_msg
        return formatted_msg
    
    def call_imagen4(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Imagen 4 API with detailed status tracking"""
        start_time = time.time()
        
        try:
            request = {"prompt": prompt, **params}
            
            self._log_status("🚀 Starting Imagen 4 generation...")
            if self.debug_mode:
                self._log_status(f"Request params: {request}", "debug")
            
            # Define queue update handler for Imagen 4
            def on_imagen4_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        status_msg = f"📝 Imagen4: {log['message']}"
                        self._log_status(status_msg)
            
            self._log_status("⏳ Submitting request to Imagen 4...")
            
            result = self.client.subscribe(
                "fal-ai/imagen4/preview/fast",
                arguments=request,
                with_logs=True,
                on_queue_update=on_imagen4_queue_update
            )
            
            elapsed_time = time.time() - start_time
            self._log_status(f"✅ Imagen 4 completed in {elapsed_time:.1f}s")
            
            if result.get('images'):
                self._log_status(f"📷 Generated {len(result['images'])} image(s)")
            else:
                self._log_status("⚠️ No images in response")
            
            return {
                "success": True, 
                "result": result,
                "elapsed_time": elapsed_time,
                "status": "completed"
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"❌ Imagen 4 failed after {elapsed_time:.1f}s: {str(e)}"
            self._log_status(error_msg)
            return {
                "success": False, 
                "error": str(e),
                "elapsed_time": elapsed_time,
                "status": "failed"
            }
    
    def call_kontext_max(self, prompt: str, image_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Kontext Max API with detailed status tracking"""
        start_time = time.time()
        
        try:
            request = {
                "prompt": prompt,
                "image_url": image_url,
                **params
            }
            
            self._log_status("🔄 Starting Kontext Max consistency generation...")
            self._log_status(f"Prompt: {prompt[:60]}..." if len(prompt) > 60 else f"Prompt: {prompt}")
            
            if self.debug_mode:
                self._log_status(f"Image URL length: {len(image_url)} chars", "debug")
                self._log_status(f"Request params: {params}", "debug")
            
            # Define queue update handler for Kontext Max
            def on_kontext_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        status_msg = f"📝 Kontext Max: {log['message']}"
                        self._log_status(status_msg)
            
            self._log_status("⏳ Submitting request to Kontext Max...")
            
            result = self.client.subscribe(
                "fal-ai/flux-pro/kontext/max",
                arguments=request,
                with_logs=True,
                on_queue_update=on_kontext_queue_update
            )
            
            elapsed_time = time.time() - start_time
            self._log_status(f"✅ Kontext Max completed in {elapsed_time:.1f}s")
            
            if result.get('images'):
                self._log_status(f"📷 Generated {len(result['images'])} variation(s)")
            else:
                self._log_status("⚠️ No images in response")
            
            return {
                "success": True, 
                "result": result,
                "elapsed_time": elapsed_time,
                "status": "completed"
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"❌ Kontext Max failed after {elapsed_time:.1f}s: {str(e)}"
            self._log_status(error_msg)
            return {
                "success": False, 
                "error": str(e),
                "elapsed_time": elapsed_time,
                "status": "failed"
            }
    
    def call_kontext_lora(self, image_url: str, style_config: Dict[str, Any], 
                         params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Kontext LoRA API for style transfer with detailed status tracking"""
        start_time = time.time()
        
        try:
            request = {
                "image_url": image_url,
                "prompt": style_config["prompt_template"],
                "loras": [{
                    "path": style_config["lora_path"],
                    "scale": style_config["weight"]
                }],
                **params
            }
            
            self._log_status(f"🎨 Starting {style_config['name']} style transfer...")
            self._log_status(f"LoRA weight: {style_config['weight']}")
            
            if self.debug_mode:
                self._log_status(f"LoRA path: {style_config['lora_path']}", "debug")
                self._log_status(f"Image URL length: {len(image_url)} chars", "debug")
                self._log_status(f"Request params: {params}", "debug")
            
            # Define queue update handler for Kontext LoRA
            def on_lora_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        status_msg = f"📝 Kontext LoRA: {log['message']}"
                        self._log_status(status_msg)
            
            self._log_status("⏳ Submitting request to Kontext LoRA...")
            
            result = self.client.subscribe(
                "fal-ai/flux-kontext-lora",
                arguments=request,
                with_logs=True,
                on_queue_update=on_lora_queue_update
            )
            
            elapsed_time = time.time() - start_time
            self._log_status(f"✅ {style_config['name']} style completed in {elapsed_time:.1f}s")
            
            if result.get('images'):
                self._log_status(f"🎭 Generated {len(result['images'])} styled image(s)")
            else:
                self._log_status("⚠️ No images in response")
            
            return {
                "success": True, 
                "result": result,
                "elapsed_time": elapsed_time,
                "status": "completed"
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"❌ {style_config['name']} style failed after {elapsed_time:.1f}s: {str(e)}"
            self._log_status(error_msg)
            return {
                "success": False, 
                "error": str(e),
                "elapsed_time": elapsed_time,
                "status": "failed"
            }

def format_progress_message(current: int, total: int, operation: str) -> str:
    """Format progress message for UI updates"""
    percentage = (current / total) * 100 if total > 0 else 0
    return f"{operation}: {current}/{total} ({percentage:.1f}%)"

def cleanup_temp_files(directory: Path, max_age_hours: int = 24) -> None:
    """Clean up temporary files older than specified hours"""
    try:
        current_time = time.time()
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    file_path.unlink()
    except Exception as e:
        print(f"Cleanup failed: {e}")

def validate_image_file(file_path: Path) -> bool:
    """Validate if file is a valid image"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def create_thumbnail(image_path: Path, output_path: Path, size: Tuple[int, int] = (200, 200)) -> bool:
    """Create a thumbnail of an image"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG for smaller file size
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            return True
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return False

def get_image_info(image_path: Path) -> Dict[str, Any]:
    """Get comprehensive image information"""
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "file_size": image_path.stat().st_size,
                "file_size_mb": image_path.stat().st_size / (1024 * 1024)
            }
    except Exception as e:
        return {
            "error": str(e),
            "file_size": image_path.stat().st_size if image_path.exists() else 0
        }

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes >= 1024 * 1024 * 1024:  # GB
        return f"{size_bytes / (1024**3):.1f} GB"
    elif size_bytes >= 1024 * 1024:  # MB
        return f"{size_bytes / (1024**2):.1f} MB"
    elif size_bytes >= 1024:  # KB
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes} bytes"

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing invalid characters"""
    import re
    # Remove invalid characters for filenames
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    # Trim underscores from ends
    safe_name = safe_name.strip('_')
    return safe_name or "unnamed"