"""Core character creation logic for the Gradio application"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Generator
from datetime import datetime

from config import DEFAULT_API_CONFIG, STYLE_CONFIGS, DEFAULT_TEST_PROMPTS
from utils import (
    APIWrapper, create_session_folder, build_character_prompt, 
    save_image_from_url, create_metadata_entry, save_metadata,
    format_progress_message, convert_image_to_data_url
)

class CharacterCreator:
    """Main class for character creation workflow"""
    
    def __init__(self, debug_mode: bool = False):
        self.api = APIWrapper(debug_mode=debug_mode)
        self.current_session = None
        self.base_image_path = None
        self.debug_mode = debug_mode
        
    def validate_setup(self) -> Tuple[bool, str]:
        """Validate API key and setup"""
        if 'FAL_KEY' not in os.environ:
            return False, "❌ FAL API key not found. Please set your API key in the environment."
        
        try:
            # Test API connection (simplified check)
            key = os.environ['FAL_KEY']
            if len(key) < 10:
                return False, "❌ Invalid API key format."
            return True, "✅ API key validated successfully."
        except Exception as e:
            return False, f"❌ API validation failed: {str(e)}"
    
    def create_base_character(self, character_config: Dict[str, Any], 
                            session_id: str, character_id: str) -> Tuple[bool, str, Optional[str]]:
        """Generate base character image using Imagen 4"""
        try:
            # Create folder structure
            base_path, consistency_path = create_session_folder(session_id, character_id)
            self.current_session = base_path
            
            # Build character prompt
            prompt = build_character_prompt(character_config)
            
            if self.debug_mode:
                print(f"[DEBUG] Generated prompt: {prompt}")
                print(f"[DEBUG] Character config: {character_config}")
            
            # Call Imagen 4 API with detailed status tracking
            response = self.api.call_imagen4(prompt, DEFAULT_API_CONFIG.imagen4_params)
            
            if not response["success"]:
                error_msg = f"❌ Imagen 4 generation failed: {response['error']}"
                if 'elapsed_time' in response:
                    error_msg += f" (took {response['elapsed_time']:.1f}s)"
                return False, error_msg, None
            
            result = response["result"]
            elapsed_time = response.get('elapsed_time', 0)
            
            # Save base image
            if result.get('images') and len(result['images']) > 0:
                image_url = result['images'][0]['url']
                base_image_path = base_path / "Base-Character.png"
                
                print(f"💾 Downloading and saving base character image...")
                
                if save_image_from_url(image_url, base_image_path):
                    self.base_image_path = base_image_path
                    
                    # Save metadata
                    metadata = create_metadata_entry(prompt, DEFAULT_API_CONFIG.imagen4_params, result, base_image_path)
                    save_metadata(metadata, base_path / "base_character_metadata.json")
                    
                    success_msg = f"✅ Base character created successfully! "
                    success_msg += f"Seed: {result.get('seed', 'N/A')}, "
                    success_msg += f"Generation time: {elapsed_time:.1f}s"
                    
                    return True, success_msg, str(base_image_path)
                else:
                    return False, "❌ Failed to save base character image", None
            else:
                return False, "❌ No images returned from Imagen 4", None
                
        except Exception as e:
            return False, f"❌ Base character creation failed: {str(e)}", None
    
    def generate_consistency_variations(self, test_prompts: List[str], 
                                      max_images: int = 10) -> Generator[Tuple[int, int, str, List[str]], None, None]:
        """Generate consistency test variations using Kontext Max"""
        if not self.base_image_path or not self.base_image_path.exists():
            yield 0, 0, "❌ No base character image found", []
            return
        
        try:
            consistency_path = self.current_session / "ConsistencyTests"
            consistency_path.mkdir(exist_ok=True)
            
            # Limit prompts to max_images
            prompts_to_process = test_prompts[:max_images]
            successful_images = []
            failed_prompts = []
            
            # Convert base image to data URL
            base_image_url = convert_image_to_data_url(self.base_image_path)
            if not base_image_url:
                yield 0, 0, "❌ Failed to convert base image to data URL", []
                return
            
            for i, prompt in enumerate(prompts_to_process, 1):
                try:
                    progress_msg = format_progress_message(i, len(prompts_to_process), "Generating variations")
                    yield i, len(prompts_to_process), progress_msg, successful_images
                    
                    # Call Kontext Max API with status tracking
                    response = self.api.call_kontext_max(prompt, base_image_url, DEFAULT_API_CONFIG.kontext_max_params)
                    
                    if response["success"]:
                        result = response["result"]
                        elapsed_time = response.get('elapsed_time', 0)
                        
                        if result.get('images') and len(result['images']) > 0:
                            image_url = result['images'][0]['url']
                            output_path = consistency_path / f"Realistic_{i:03d}.png"
                            
                            print(f"💾 Saving variation {i}...")
                            
                            if save_image_from_url(image_url, output_path):
                                successful_images.append(str(output_path))
                                
                                # Save metadata with timing info
                                metadata = create_metadata_entry(prompt, DEFAULT_API_CONFIG.kontext_max_params, result, output_path)
                                metadata['generation_time'] = elapsed_time
                                metadata_path = consistency_path / f"Realistic_{i:03d}_metadata.json"
                                save_metadata(metadata, metadata_path)
                                
                                print(f"✅ Variation {i} completed in {elapsed_time:.1f}s")
                            else:
                                print(f"❌ Failed to save variation {i}")
                                failed_prompts.append((i, prompt))
                        else:
                            print(f"❌ No images returned for variation {i}")
                            failed_prompts.append((i, prompt))
                    else:
                        error_msg = f"❌ API call failed for variation {i}: {response['error']}"
                        if 'elapsed_time' in response:
                            error_msg += f" (took {response['elapsed_time']:.1f}s)"
                        print(error_msg)
                        failed_prompts.append((i, prompt))
                    
                except Exception as e:
                    print(f"Failed to generate variation {i}: {e}")
                    failed_prompts.append((i, prompt))
                    continue
            
            # Save session metadata
            session_metadata = {
                "total_prompts": len(prompts_to_process),
                "successful_generations": len(successful_images),
                "failed_generations": len(failed_prompts),
                "successful_images": successful_images,
                "failed_prompts": failed_prompts,
                "timestamp": datetime.now().isoformat()
            }
            save_metadata(session_metadata, consistency_path / "consistency_session_metadata.json")
            
            final_msg = f"✅ Generated {len(successful_images)} consistency variations ({len(failed_prompts)} failed)"
            yield len(prompts_to_process), len(prompts_to_process), final_msg, successful_images
            
        except Exception as e:
            yield 0, 0, f"❌ Consistency generation failed: {str(e)}", []
    
    def apply_style_transfer(self, style_name: str, 
                           source_images: List[str]) -> Generator[Tuple[int, int, str, List[str]], None, None]:
        """Apply LoRA style transfer to generated images"""
        if not source_images:
            yield 0, 0, "❌ No source images for style transfer", []
            return
        
        try:
            style_config = STYLE_CONFIGS.get(style_name)
            if not style_config:
                yield 0, 0, f"❌ Unknown style: {style_name}", []
                return
            
            styles_path = self.current_session / "Styles" / style_config["name"]
            styles_path.mkdir(parents=True, exist_ok=True)
            
            styled_images = []
            failed_transfers = []
            
            for i, source_image_path in enumerate(source_images, 1):
                try:
                    progress_msg = format_progress_message(i, len(source_images), f"Applying {style_config['name']} style")
                    yield i, len(source_images), progress_msg, styled_images
                    
                    # Convert source image to data URL
                    source_image_url = convert_image_to_data_url(Path(source_image_path))
                    if not source_image_url:
                        print(f"Failed to convert {source_image_path} to data URL")
                        failed_transfers.append((i, source_image_path))
                        continue
                    
                    # Call Kontext LoRA API with status tracking
                    response = self.api.call_kontext_lora(source_image_url, style_config, DEFAULT_API_CONFIG.kontext_lora_params)
                    
                    if response["success"]:
                        result = response["result"]
                        elapsed_time = response.get('elapsed_time', 0)
                        
                        if result.get('images') and len(result['images']) > 0:
                            styled_image_url = result['images'][0]['url']
                            output_path = styles_path / f"{style_config['name']}_{i:03d}.png"
                            
                            print(f"💾 Saving {style_config['name']} styled image {i}...")
                            
                            if save_image_from_url(styled_image_url, output_path):
                                styled_images.append(str(output_path))
                                
                                # Save metadata with timing info
                                metadata = create_metadata_entry(
                                    style_config["prompt_template"], 
                                    DEFAULT_API_CONFIG.kontext_lora_params, 
                                    result, 
                                    output_path
                                )
                                metadata['generation_time'] = elapsed_time
                                metadata['style_name'] = style_config['name']
                                metadata_path = styles_path / f"{style_config['name']}_{i:03d}_metadata.json"
                                save_metadata(metadata, metadata_path)
                                
                                print(f"✅ {style_config['name']} style {i} completed in {elapsed_time:.1f}s")
                            else:
                                print(f"❌ Failed to save {style_config['name']} styled image {i}")
                                failed_transfers.append((i, source_image_path))
                        else:
                            print(f"❌ No styled images returned for {style_config['name']} {i}")
                            failed_transfers.append((i, source_image_path))
                    else:
                        error_msg = f"❌ {style_config['name']} style API call failed for image {i}: {response['error']}"
                        if 'elapsed_time' in response:
                            error_msg += f" (took {response['elapsed_time']:.1f}s)"
                        print(error_msg)
                        failed_transfers.append((i, source_image_path))
                    
                except Exception as e:
                    print(f"Failed to apply style to image {i}: {e}")
                    failed_transfers.append((i, source_image_path))
                    continue
            
            # Save style transfer session metadata
            style_session_metadata = {
                "style_name": style_config["name"],
                "style_config": style_config,
                "total_source_images": len(source_images),
                "successful_transfers": len(styled_images),
                "failed_transfers": len(failed_transfers),
                "styled_images": styled_images,
                "failed_transfers_list": failed_transfers,
                "timestamp": datetime.now().isoformat()
            }
            save_metadata(style_session_metadata, styles_path / f"{style_config['name']}_session_metadata.json")
            
            final_msg = f"✅ Applied {style_config['name']} style to {len(styled_images)} images ({len(failed_transfers)} failed)"
            yield len(source_images), len(source_images), final_msg, styled_images
            
        except Exception as e:
            yield 0, 0, f"❌ Style transfer failed: {str(e)}", []
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of current generation session"""
        if not self.current_session:
            return {"status": "No active session"}
        
        try:
            summary = {
                "session_path": str(self.current_session),
                "base_image": str(self.base_image_path) if self.base_image_path else None,
                "timestamp": datetime.now().isoformat(),
                "images_count": {}
            }
            
            # Count generated images
            if self.base_image_path and self.base_image_path.exists():
                summary["images_count"]["base"] = 1
            
            consistency_path = self.current_session / "ConsistencyTests"
            if consistency_path.exists():
                realistic_images = list(consistency_path.glob("Realistic_*.png"))
                summary["images_count"]["realistic_variations"] = len(realistic_images)
            
            styles_path = self.current_session / "Styles"
            if styles_path.exists():
                for style_name, style_config in STYLE_CONFIGS.items():
                    style_folder = styles_path / style_config["name"]
                    if style_folder.exists():
                        style_images = list(style_folder.glob("*.png"))
                        summary["images_count"][f"{style_name}_style"] = len(style_images)
            
            total_images = sum(summary["images_count"].values())
            summary["images_count"]["total"] = total_images
            
            return summary
            
        except Exception as e:
            return {"status": f"Error generating summary: {str(e)}"}
    
    def get_all_generated_images(self) -> List[Tuple[str, str]]:
        """Get all images from current session for gallery display"""
        if not self.current_session:
            return []
        
        images = []
        
        try:
            # Base image
            if self.base_image_path and self.base_image_path.exists():
                images.append((str(self.base_image_path), "Base Character"))
            
            # Realistic variations
            consistency_path = self.current_session / "ConsistencyTests"
            if consistency_path.exists():
                for img_path in sorted(consistency_path.glob("Realistic_*.png")):
                    images.append((str(img_path), f"Realistic Variation"))
            
            # Styled images
            styles_path = self.current_session / "Styles"
            if styles_path.exists():
                for style_name, style_config in STYLE_CONFIGS.items():
                    style_folder = styles_path / style_config["name"]
                    if style_folder.exists():
                        for img_path in sorted(style_folder.glob("*.png")):
                            images.append((str(img_path), f"{style_config['name']} Style"))
            
            return images
            
        except Exception as e:
            print(f"Error collecting images: {e}")
            return []