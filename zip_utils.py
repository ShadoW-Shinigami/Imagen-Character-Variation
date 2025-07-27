"""ZIP utilities for character downloading and packaging"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Generator
from datetime import datetime
import shutil

from character_manager import CharacterInfo

class CharacterZipper:
    """Handles ZIP creation and packaging for characters"""
    
    def __init__(self):
        self.temp_dir = None
    
    def create_character_zip(self, char_info: CharacterInfo, 
                           include_metadata: bool = True) -> Tuple[bool, str, Optional[str]]:
        """Create a ZIP file for a single character"""
        try:
            # Create temporary file for ZIP
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{char_info.character_id}_{timestamp}.zip"
            
            # Create temporary ZIP file
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add base character image
                if char_info.base_image_path and char_info.base_image_path.exists():
                    zipf.write(char_info.base_image_path, char_info.base_image_path.name)
                
                # Add base metadata
                if include_metadata and char_info.base_metadata:
                    metadata_json = json.dumps(char_info.base_metadata, indent=2)
                    zipf.writestr("base_character_metadata.json", metadata_json)
                
                # Add consistency test images
                consistency_path = char_info.path / "ConsistencyTests"
                if consistency_path.exists():
                    for img_file in consistency_path.glob("*.png"):
                        arcname = f"ConsistencyTests/{img_file.name}"
                        zipf.write(img_file, arcname)
                    
                    # Add consistency metadata files
                    if include_metadata:
                        for meta_file in consistency_path.glob("*.json"):
                            arcname = f"ConsistencyTests/{meta_file.name}"
                            zipf.write(meta_file, arcname)
                
                # Add styled images
                styles_path = char_info.path / "Styles"
                if styles_path.exists():
                    for style_dir in styles_path.iterdir():
                        if style_dir.is_dir():
                            style_name = style_dir.name
                            
                            # Add styled images
                            for img_file in style_dir.glob("*.png"):
                                arcname = f"Styles/{style_name}/{img_file.name}"
                                zipf.write(img_file, arcname)
                            
                            # Add style metadata
                            if include_metadata:
                                for meta_file in style_dir.glob("*.json"):
                                    arcname = f"Styles/{style_name}/{meta_file.name}"
                                    zipf.write(meta_file, arcname)
                
                # Create comprehensive character summary
                if include_metadata:
                    summary = self._create_character_summary(char_info)
                    zipf.writestr("character_summary.json", json.dumps(summary, indent=2))
                    
                    # Create README
                    readme_content = self._create_readme(char_info)
                    zipf.writestr("README.txt", readme_content)
            
            # Get file size
            file_size = os.path.getsize(temp_zip_path)
            size_mb = file_size / (1024 * 1024)
            
            success_msg = f"✅ ZIP created successfully: {zip_filename} ({size_mb:.1f} MB)"
            return True, success_msg, temp_zip_path
            
        except Exception as e:
            return False, f"❌ Error creating ZIP: {str(e)}", None
    
    def create_batch_zip(self, characters: List[CharacterInfo], 
                        include_metadata: bool = True) -> Tuple[bool, str, Optional[str]]:
        """Create a ZIP file containing multiple characters"""
        try:
            if not characters:
                return False, "❌ No characters selected", None
            
            # Create ZIP filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"Characters_Batch_{timestamp}.zip"
            
            # Create temporary ZIP file
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                # Add each character in its own folder
                for char_info in characters:
                    char_folder = f"{char_info.session_id}_{char_info.character_id}"
                    
                    # Add base character image
                    if char_info.base_image_path and char_info.base_image_path.exists():
                        arcname = f"{char_folder}/{char_info.base_image_path.name}"
                        zipf.write(char_info.base_image_path, arcname)
                    
                    # Add base metadata
                    if include_metadata and char_info.base_metadata:
                        metadata_json = json.dumps(char_info.base_metadata, indent=2)
                        zipf.writestr(f"{char_folder}/base_character_metadata.json", metadata_json)
                    
                    # Add consistency test images
                    consistency_path = char_info.path / "ConsistencyTests"
                    if consistency_path.exists():
                        for img_file in consistency_path.glob("*.png"):
                            arcname = f"{char_folder}/ConsistencyTests/{img_file.name}"
                            zipf.write(img_file, arcname)
                        
                        if include_metadata:
                            for meta_file in consistency_path.glob("*.json"):
                                arcname = f"{char_folder}/ConsistencyTests/{meta_file.name}"
                                zipf.write(meta_file, arcname)
                    
                    # Add styled images
                    styles_path = char_info.path / "Styles"
                    if styles_path.exists():
                        for style_dir in styles_path.iterdir():
                            if style_dir.is_dir():
                                style_name = style_dir.name
                                
                                for img_file in style_dir.glob("*.png"):
                                    arcname = f"{char_folder}/Styles/{style_name}/{img_file.name}"
                                    zipf.write(img_file, arcname)
                                
                                if include_metadata:
                                    for meta_file in style_dir.glob("*.json"):
                                        arcname = f"{char_folder}/Styles/{style_name}/{meta_file.name}"
                                        zipf.write(meta_file, arcname)
                    
                    # Add character summary
                    if include_metadata:
                        summary = self._create_character_summary(char_info)
                        zipf.writestr(f"{char_folder}/character_summary.json", 
                                    json.dumps(summary, indent=2))
                
                # Add batch summary
                if include_metadata:
                    batch_summary = self._create_batch_summary(characters)
                    zipf.writestr("batch_summary.json", json.dumps(batch_summary, indent=2))
                    
                    # Create batch README
                    readme_content = self._create_batch_readme(characters)
                    zipf.writestr("README.txt", readme_content)
            
            # Get file size
            file_size = os.path.getsize(temp_zip_path)
            size_mb = file_size / (1024 * 1024)
            
            success_msg = f"✅ Batch ZIP created: {len(characters)} characters ({size_mb:.1f} MB)"
            return True, success_msg, temp_zip_path
            
        except Exception as e:
            return False, f"❌ Error creating batch ZIP: {str(e)}", None
    
    def _create_character_summary(self, char_info: CharacterInfo) -> Dict[str, Any]:
        """Create comprehensive character summary"""
        return {
            "character_info": {
                "session_id": char_info.session_id,
                "character_id": char_info.character_id,
                "creation_date": char_info.creation_date.isoformat(),
                "prompt": char_info.prompt
            },
            "image_statistics": {
                "base_image": 1 if char_info.base_image_path and char_info.base_image_path.exists() else 0,
                "realistic_variations": char_info.realistic_count,
                "styled_images": char_info.styled_counts,
                "total_images": char_info.total_images
            },
            "character_config": char_info.character_config or {},
            "generation_metadata": char_info.base_metadata or {},
            "export_info": {
                "export_date": datetime.now().isoformat(),
                "export_tool": "AI Character Creation Studio"
            }
        }
    
    def _create_batch_summary(self, characters: List[CharacterInfo]) -> Dict[str, Any]:
        """Create summary for batch of characters"""
        total_images = sum(char.total_images for char in characters)
        
        # Aggregate style counts
        style_totals = {}
        for char in characters:
            for style_name, count in char.styled_counts.items():
                style_totals[style_name] = style_totals.get(style_name, 0) + count
        
        # Date range
        dates = [char.creation_date for char in characters]
        
        return {
            "batch_info": {
                "total_characters": len(characters),
                "export_date": datetime.now().isoformat(),
                "export_tool": "AI Character Creation Studio"
            },
            "aggregate_statistics": {
                "total_images": total_images,
                "total_realistic_variations": sum(char.realistic_count for char in characters),
                "style_breakdown": style_totals,
                "creation_date_range": {
                    "earliest": min(dates).isoformat() if dates else None,
                    "latest": max(dates).isoformat() if dates else None
                }
            },
            "characters": [
                {
                    "session_id": char.session_id,
                    "character_id": char.character_id,
                    "creation_date": char.creation_date.isoformat(),
                    "image_count": char.total_images,
                    "prompt": char.prompt
                }
                for char in characters
            ]
        }
    
    def _create_readme(self, char_info: CharacterInfo) -> str:
        """Create README content for character ZIP"""
        return f"""AI Character Creation Studio - Character Export
==================================================

Character Information:
- Session ID: {char_info.session_id}
- Character ID: {char_info.character_id}
- Creation Date: {char_info.creation_date.strftime('%Y-%m-%d %H:%M:%S')}
- Total Images: {char_info.total_images}

Generated Images:
- Base Character: {'✓' if char_info.base_image_path and char_info.base_image_path.exists() else '✗'}
- Realistic Variations: {char_info.realistic_count}
- Styled Images: {dict(char_info.styled_counts)}

Folder Structure:
├── Base-Character.png (or Base-Image.png)
├── base_character_metadata.json
├── ConsistencyTests/
│   ├── Realistic_001.png
│   ├── Realistic_002.png
│   └── ... (metadata files)
└── Styles/
    ├── Studio Ghibli/
    └── Rick & Morty/

Files Description:
- character_summary.json: Complete character metadata and statistics
- ConsistencyTests/: Character variations maintaining consistency
- Styles/: Stylized versions using different artistic styles
- *_metadata.json: Generation parameters and API responses

Generated by: AI Character Creation Studio
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _create_batch_readme(self, characters: List[CharacterInfo]) -> str:
        """Create README content for batch ZIP"""
        total_images = sum(char.total_images for char in characters)
        
        character_list = "\n".join([
            f"- {char.character_id} ({char.total_images} images) - {char.creation_date.strftime('%Y-%m-%d')}"
            for char in characters
        ])
        
        return f"""AI Character Creation Studio - Batch Character Export
========================================================

Batch Information:
- Total Characters: {len(characters)}
- Total Images: {total_images}
- Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Included Characters:
{character_list}

Folder Structure:
├── batch_summary.json (batch metadata)
├── README.txt (this file)
└── [Session_ID]_[Character_ID]/
    ├── Base-Character.png
    ├── character_summary.json
    ├── ConsistencyTests/
    └── Styles/

Each character folder contains:
- Base character image
- Realistic variations (consistency tests)
- Styled versions (Studio Ghibli, Rick & Morty, etc.)
- Complete metadata and generation parameters

Generated by: AI Character Creation Studio
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def cleanup_temp_file(self, temp_path: str) -> None:
        """Clean up temporary ZIP file"""
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"Warning: Could not clean up temp file {temp_path}: {e}")
    
    def get_estimated_zip_size(self, characters: List[CharacterInfo]) -> Tuple[int, str]:
        """Estimate ZIP file size for characters"""
        total_size = 0
        
        try:
            for char in characters:
                # Base image
                if char.base_image_path and char.base_image_path.exists():
                    total_size += char.base_image_path.stat().st_size
                
                # Consistency images
                consistency_path = char.path / "ConsistencyTests"
                if consistency_path.exists():
                    for img_file in consistency_path.glob("*.png"):
                        total_size += img_file.stat().st_size
                
                # Styled images
                styles_path = char.path / "Styles"
                if styles_path.exists():
                    for style_dir in styles_path.iterdir():
                        if style_dir.is_dir():
                            for img_file in style_dir.glob("*.png"):
                                total_size += img_file.stat().st_size
            
            # Account for compression (estimate 70% of original size)
            estimated_zip_size = int(total_size * 0.7)
            
            # Format size
            if estimated_zip_size > 1024 * 1024 * 1024:  # GB
                size_str = f"{estimated_zip_size / (1024**3):.1f} GB"
            elif estimated_zip_size > 1024 * 1024:  # MB
                size_str = f"{estimated_zip_size / (1024**2):.1f} MB"
            else:  # KB
                size_str = f"{estimated_zip_size / 1024:.1f} KB"
            
            return estimated_zip_size, size_str
            
        except Exception as e:
            return 0, "Unknown"