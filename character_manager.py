"""Character management and discovery utilities"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import glob

@dataclass
class CharacterInfo:
    """Data class for character information"""
    session_id: str
    character_id: str
    path: Path
    creation_date: datetime
    base_image_path: Optional[Path]
    base_metadata: Optional[Dict[str, Any]]
    
    # Image counts
    realistic_count: int = 0
    styled_counts: Dict[str, int] = None
    total_images: int = 0
    
    # Generation info
    character_config: Optional[Dict[str, Any]] = None
    generation_time: Optional[float] = None
    prompt: Optional[str] = None
    
    def __post_init__(self):
        if self.styled_counts is None:
            self.styled_counts = {}

class CharacterManager:
    """Manages character discovery, metadata, and operations"""
    
    def __init__(self, root_directory: str = ".", debug: bool = False):
        self.root_directory = Path(root_directory)
        self._characters_cache = None
        self._last_scan_time = None
        self.debug = debug
        
        # Only scan the specified root directory
        self.scan_locations = [Path(root_directory).resolve()]
        
        if self.debug:
            print(f"[DEBUG] Scanning only root directory: {self.scan_locations[0]}")
    
    def discover_characters(self, force_refresh: bool = False) -> List[CharacterInfo]:
        """Discover all character sessions in the root directory"""
        current_time = datetime.now()
        
        # Use cache if available and recent (within 30 seconds)
        if (not force_refresh and 
            self._characters_cache is not None and 
            self._last_scan_time is not None and 
            (current_time - self._last_scan_time).seconds < 30):
            return self._characters_cache
        
        characters = []
        
        # Scan all configured locations
        for scan_location in self.scan_locations:
            if not scan_location.exists():
                if self.debug:
                    print(f"[DEBUG] Scan location does not exist: {scan_location}")
                continue
                
            if self.debug:
                print(f"[DEBUG] Scanning location: {scan_location}")
            
            try:
                location_characters = self._scan_location(scan_location)
                characters.extend(location_characters)
                if self.debug:
                    print(f"[DEBUG] Found {len(location_characters)} characters in {scan_location}")
            except Exception as e:
                print(f"Error scanning location {scan_location}: {e}")
                continue
        
        # Remove duplicates (same session_id + character_id)
        seen = set()
        unique_characters = []
        for char in characters:
            char_key = (char.session_id, char.character_id)
            if char_key not in seen:
                seen.add(char_key)
                unique_characters.append(char)
            elif self.debug:
                print(f"[DEBUG] Skipping duplicate character: {char.session_id}/{char.character_id}")
        
        characters = unique_characters
        
        # Sort by creation date (newest first)
        characters.sort(key=lambda x: x.creation_date, reverse=True)
        
        # Update cache
        self._characters_cache = characters
        self._last_scan_time = current_time
        
        if self.debug:
            print(f"[DEBUG] Total unique characters found: {len(characters)}")
        
        return characters
    
    def _scan_location(self, location: Path) -> List[CharacterInfo]:
        """Scan a specific location for characters"""
        characters = []
        
        try:            
            # Pattern 1: Standard format - Session_*/Char_*
            session_count = 0
            for session_path in location.glob("Session_*"):
                if not session_path.is_dir():
                    continue
                
                session_count += 1
                session_id = session_path.name
                if self.debug:
                    print(f"[DEBUG] Found session directory: {session_id}")
                
                # Look for character directories within session
                char_count = 0
                for char_path in session_path.glob("Char_*"):
                    if not char_path.is_dir():
                        continue
                    
                    char_count += 1
                    character_id = char_path.name
                    if self.debug:
                        print(f"[DEBUG] Found character directory: {session_id}/{character_id}")
                    
                    try:
                        char_info = self._analyze_character_directory(session_id, character_id, char_path)
                        if char_info:
                            characters.append(char_info)
                            if self.debug:
                                print(f"[DEBUG] Successfully analyzed character: {character_id} ({char_info.total_images} images)")
                    except Exception as e:
                        print(f"Error analyzing character {session_id}/{character_id}: {e}")
                        continue
                
                if self.debug and char_count == 0:
                    print(f"[DEBUG] No character directories found in {session_id}")
            
            if self.debug:
                print(f"[DEBUG] Found {session_count} session directories with standard pattern")
            
            # Pattern 2: Non-standard format - numeric directories with character names
            for potential_session in location.iterdir():
                if not potential_session.is_dir():
                    continue
                
                # Skip if it matches standard pattern (already processed)
                if potential_session.name.startswith("Session_"):
                    continue
                
                # Skip system directories
                if potential_session.name.startswith('.') or potential_session.name in ['__pycache__']:
                    continue
                
                session_id = potential_session.name
                if self.debug:
                    print(f"[DEBUG] Checking non-standard directory: {session_id}")
                
                # Look for character directories (any subdirectory with character files)
                for char_path in potential_session.iterdir():
                    if not char_path.is_dir():
                        continue
                    
                    character_id = char_path.name
                    
                    # Check if this looks like a character directory (has base image or metadata)
                    has_base_image = any(char_path.glob("Base-*.png"))
                    has_metadata = any(char_path.glob("*metadata.json"))
                    
                    if has_base_image or has_metadata:
                        if self.debug:
                            print(f"[DEBUG] Found non-standard character: {session_id}/{character_id}")
                        
                        try:
                            char_info = self._analyze_character_directory(session_id, character_id, char_path)
                            if char_info:
                                characters.append(char_info)
                                if self.debug:
                                    print(f"[DEBUG] Successfully analyzed non-standard character: {character_id} ({char_info.total_images} images)")
                        except Exception as e:
                            if self.debug:
                                print(f"[DEBUG] Error analyzing non-standard character {session_id}/{character_id}: {e}")
                            continue
            
            return characters
            
        except Exception as e:
            print(f"Error scanning location {location}: {e}")
            return []
    
    def _analyze_character_directory(self, session_id: str, character_id: str, char_path: Path) -> Optional[CharacterInfo]:
        """Analyze a character directory and extract information"""
        try:
            # Get directory creation time
            creation_date = datetime.fromtimestamp(char_path.stat().st_ctime)
            
            # Initialize character info
            char_info = CharacterInfo(
                session_id=session_id,
                character_id=character_id,
                path=char_path,
                creation_date=creation_date,
                base_image_path=None,
                base_metadata=None
            )
            
            # Look for base character image
            base_image_candidates = [
                "Base-Character.png",
                "Base-Image.png"
            ]
            
            for candidate in base_image_candidates:
                base_path = char_path / candidate
                if base_path.exists():
                    char_info.base_image_path = base_path
                    break
            
            # Load base character metadata
            base_metadata_path = char_path / "base_character_metadata.json"
            if not base_metadata_path.exists():
                base_metadata_path = char_path / "base_image_metadata.json"
            
            if base_metadata_path.exists():
                try:
                    with open(base_metadata_path, 'r') as f:
                        char_info.base_metadata = json.load(f)
                    
                    # Extract character config and prompt
                    if char_info.base_metadata:
                        char_info.prompt = char_info.base_metadata.get('prompt')
                        if 'parameters' in char_info.base_metadata:
                            # Try to extract character config from prompt or other metadata
                            char_info.character_config = {}
                except Exception as e:
                    print(f"Error loading base metadata: {e}")
            
            # Count realistic variations
            consistency_path = char_path / "ConsistencyTests"
            if consistency_path.exists():
                realistic_images = list(consistency_path.glob("Realistic_*.png"))
                char_info.realistic_count = len(realistic_images)
            
            # Count styled images
            styles_path = char_path / "Styles"
            if styles_path.exists():
                for style_dir in styles_path.iterdir():
                    if style_dir.is_dir():
                        style_name = style_dir.name
                        styled_images = list(style_dir.glob("*.png"))
                        char_info.styled_counts[style_name] = len(styled_images)
            
            # Calculate total images
            char_info.total_images = (
                (1 if char_info.base_image_path and char_info.base_image_path.exists() else 0) +
                char_info.realistic_count +
                sum(char_info.styled_counts.values())
            )
            
            # Only return if there are actually images
            if char_info.total_images > 0:
                return char_info
            
            return None
            
        except Exception as e:
            print(f"Error analyzing character directory {char_path}: {e}")
            return None
    
    def get_character_by_id(self, session_id: str, character_id: str) -> Optional[CharacterInfo]:
        """Get specific character by session and character ID"""
        characters = self.discover_characters()
        
        for char in characters:
            if char.session_id == session_id and char.character_id == character_id:
                return char
        
        return None
    
    def get_character_preview_images(self, char_info: CharacterInfo, max_previews: int = 6) -> List[Tuple[str, str]]:
        """Get preview images for a character (path, description)"""
        previews = []
        
        try:
            # Add base image
            if char_info.base_image_path and char_info.base_image_path.exists():
                previews.append((str(char_info.base_image_path), "Base Character"))
            
            # Add some realistic variations
            consistency_path = char_info.path / "ConsistencyTests"
            if consistency_path.exists():
                realistic_images = sorted(list(consistency_path.glob("Realistic_*.png")))[:3]
                for i, img_path in enumerate(realistic_images, 1):
                    previews.append((str(img_path), f"Variation {i}"))
            
            # Add some styled images
            styles_path = char_info.path / "Styles"
            if styles_path.exists():
                for style_name, count in list(char_info.styled_counts.items())[:2]:  # Max 2 styles
                    style_dir = styles_path / style_name
                    if style_dir.exists():
                        style_images = sorted(list(style_dir.glob("*.png")))[:1]  # 1 per style
                        for img_path in style_images:
                            previews.append((str(img_path), f"{style_name} Style"))
            
            return previews[:max_previews]
            
        except Exception as e:
            print(f"Error getting preview images: {e}")
            return previews
    
    def get_character_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about all characters"""
        characters = self.discover_characters()
        
        if not characters:
            return {
                "total_characters": 0,
                "total_images": 0,
                "total_sessions": 0,
                "creation_date_range": None,
                "style_breakdown": {}
            }
        
        total_images = sum(char.total_images for char in characters)
        sessions = set(char.session_id for char in characters)
        
        # Style breakdown
        style_breakdown = {}
        for char in characters:
            for style_name, count in char.styled_counts.items():
                style_breakdown[style_name] = style_breakdown.get(style_name, 0) + count
        
        # Date range
        dates = [char.creation_date for char in characters]
        date_range = {
            "earliest": min(dates).isoformat(),
            "latest": max(dates).isoformat()
        } if dates else None
        
        return {
            "total_characters": len(characters),
            "total_images": total_images,
            "total_sessions": len(sessions),
            "creation_date_range": date_range,
            "style_breakdown": style_breakdown,
            "average_images_per_character": total_images / len(characters) if characters else 0
        }
    
    def delete_character(self, char_info: CharacterInfo) -> Tuple[bool, str]:
        """Delete a character and all its files"""
        try:
            import shutil
            
            if char_info.path.exists():
                shutil.rmtree(char_info.path)
                
                # Clear cache to force refresh
                self._characters_cache = None
                
                return True, f"✅ Character {char_info.character_id} deleted successfully"
            else:
                return False, f"❌ Character directory not found: {char_info.path}"
                
        except Exception as e:
            return False, f"❌ Error deleting character: {str(e)}"
    
    def refresh_characters(self) -> List[CharacterInfo]:
        """Force refresh character list"""
        return self.discover_characters(force_refresh=True)