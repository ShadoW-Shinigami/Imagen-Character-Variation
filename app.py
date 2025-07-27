"""Modern Gradio Character Creation Interface"""

import os
import gradio as gr
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import time

from config import (
    CHARACTER_ETHNICITIES, CHARACTER_GENDERS, HAIR_COLORS, EYE_COLORS,
    BUILD_TYPES, HEIGHT_TYPES, AGE_RANGES, CLOTHING_STYLES,
    STYLE_CONFIGS, DEFAULT_TEST_PROMPTS, UI_CONFIG
)
from character_creator import CharacterCreator
from utils import validate_api_key, create_thumbnail, format_file_size
from character_manager import CharacterManager, CharacterInfo
from zip_utils import CharacterZipper

# Custom Seafoam Theme
class SeafoamTheme(gr.themes.Base):
    """Custom modern theme with sea-inspired colors"""
    def __init__(self):
        super().__init__(
            primary_hue=gr.themes.colors.teal,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.gray,
            font=gr.themes.GoogleFont("Inter"),
            font_mono=gr.themes.GoogleFont("JetBrains Mono")
        )

# Initialize the character creator (debug mode will be toggled by UI)
creator = CharacterCreator(debug_mode=False)
char_manager = CharacterManager(debug=False)  # Disable debug for production
char_zipper = CharacterZipper()
seafoam_theme = SeafoamTheme()

def validate_setup():
    """Validate API setup"""
    success, message = validate_api_key()
    return message

def toggle_debug_mode(debug_enabled):
    """Toggle debug mode for the character creator"""
    global creator
    creator = CharacterCreator(debug_mode=debug_enabled)
    status_msg = f"🔧 Debug mode {'enabled' if debug_enabled else 'disabled'}"
    if debug_enabled:
        status_msg += "\nDetailed API logs and timing will be shown during generation."
    return status_msg

def create_character(ethnicity, gender, age_range, hair_color, eye_color, 
                    build, height, clothing, facial_features, session_id, character_id):
    """Create base character image"""
    # Validate inputs
    if not all([ethnicity, gender, age_range, hair_color, eye_color, build, height, clothing]):
        return "❌ Please fill in all required character details", None, ""
    
    if not session_id.strip():
        session_id = f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not character_id.strip():
        character_id = f"Character_{datetime.now().strftime('%H%M%S')}"
    
    # Build character config
    character_config = {
        "ethnicity": ethnicity,
        "gender": gender,
        "age": age_range,
        "hair_color": hair_color,
        "eye_color": eye_color,
        "build": build,
        "height": height,
        "clothing": clothing,
        "facial_features": facial_features or "friendly expression"
    }
    
    # Create character
    success, message, image_path = creator.create_base_character(
        character_config, session_id, character_id
    )
    
    return message, image_path if success else None, session_id

def generate_variations(test_prompts_text, max_images, progress=gr.Progress()):
    """Generate consistency test variations"""
    if not test_prompts_text.strip():
        test_prompts = DEFAULT_TEST_PROMPTS[:max_images]
    else:
        test_prompts = [p.strip() for p in test_prompts_text.strip().split('\n') if p.strip()]
    
    generated_images = []
    
    for current, total, message, images in creator.generate_consistency_variations(test_prompts, max_images):
        progress(current / total if total > 0 else 0, desc=message)
        generated_images = images
        time.sleep(0.1)  # Smooth progress updates
    
    return message, generated_images

def apply_style(style_name, source_images, progress=gr.Progress()):
    """Apply style transfer to images"""
    if not source_images:
        return "❌ No source images available for style transfer", []
    
    # Handle Gradio Gallery format - convert tuples to string paths
    if isinstance(source_images, list) and source_images:
        source_paths = []
        for img in source_images:
            if isinstance(img, (tuple, list)):
                # Extract the first element (image path) from tuple/list
                source_paths.append(str(img[0]))
            else:
                # Already a string path
                source_paths.append(str(img))
    else:
        source_paths = source_images
    
    styled_images = []
    
    for current, total, message, images in creator.apply_style_transfer(style_name, source_paths):
        progress(current / total if total > 0 else 0, desc=message)
        styled_images = images
        time.sleep(0.1)
    
    return message, styled_images

def get_session_summary():
    """Get current session summary"""
    summary = creator.get_generation_summary()
    
    # Check if there's an error status
    if "status" in summary:
        if summary["status"] == "No active session":
            return "ℹ️ No active generation session"
        elif summary["status"].startswith("Error"):
            return f"❌ {summary['status']}"
    
    # Check if we have valid session data
    if "session_path" not in summary or "images_count" not in summary:
        return "ℹ️ No active generation session"
    
    # Format summary
    lines = [
        f"📁 Session: {summary['session_path']}",
        f"⏰ Generated: {summary.get('timestamp', 'Unknown')[:19]}",
        "",
        "📊 Images Generated:"
    ]
    
    for img_type, count in summary['images_count'].items():
        if img_type != 'total' and count > 0:
            lines.append(f"  • {img_type.replace('_', ' ').title()}: {count}")
    
    lines.append(f"\n🎯 Total Images: {summary['images_count'].get('total', 0)}")
    
    return "\n".join(lines)

def refresh_gallery():
    """Refresh the gallery with all generated images"""
    images = creator.get_all_generated_images()
    return images

def refresh_character_library():
    """Refresh the character library and return character grid data"""
    characters = char_manager.discover_characters()
    
    if not characters:
        return [], "📭 No characters found. Create some characters first!"
    
    # Prepare character grid data
    character_grid = []
    for char in characters:
        preview_images = char_manager.get_character_preview_images(char, max_previews=3)
        
        # Create character card info
        card_info = {
            "session_id": char.session_id,
            "character_id": char.character_id,
            "creation_date": char.creation_date.strftime("%Y-%m-%d %H:%M"),
            "total_images": char.total_images,
            "realistic_count": char.realistic_count,
            "styled_counts": dict(char.styled_counts),
            "preview_images": preview_images,
            "prompt": char.prompt or "No prompt available"
        }
        character_grid.append(card_info)
    
    # Create status message
    total_chars = len(characters)
    total_images = sum(char.total_images for char in characters)
    status_msg = f"📚 Found {total_chars} characters with {total_images} total images"
    
    return character_grid, status_msg

def download_character_zip(character_data, include_metadata=True):
    """Create and download ZIP file for selected character"""
    if not character_data:
        return "❌ No character selected", None
    
    try:
        # Find the character
        char = char_manager.get_character_by_id(
            character_data["session_id"], 
            character_data["character_id"]
        )
        
        if not char:
            return "❌ Character not found", None
        
        # Create ZIP
        success, message, zip_path = char_zipper.create_character_zip(char, include_metadata)
        
        if success and zip_path:
            return message, zip_path
        else:
            return message, None
            
    except Exception as e:
        return f"❌ Error creating ZIP: {str(e)}", None

def download_batch_zip(selected_characters, include_metadata=True):
    """Create and download ZIP file for multiple characters"""
    if not selected_characters:
        return "❌ No characters selected", None
    
    try:
        # Get character objects
        characters = []
        for char_data in selected_characters:
            char = char_manager.get_character_by_id(
                char_data["session_id"], 
                char_data["character_id"]
            )
            if char:
                characters.append(char)
        
        if not characters:
            return "❌ No valid characters found", None
        
        # Create batch ZIP
        success, message, zip_path = char_zipper.create_batch_zip(characters, include_metadata)
        
        if success and zip_path:
            return message, zip_path
        else:
            return message, None
            
    except Exception as e:
        return f"❌ Error creating batch ZIP: {str(e)}", None

def get_character_details(character_data):
    """Get detailed information about a character"""
    if not character_data:
        return "No character selected"
    
    try:
        char = char_manager.get_character_by_id(
            character_data["session_id"], 
            character_data["character_id"]
        )
        
        if not char:
            return "Character not found"
        
        # Format detailed info
        details = [
            f"**Character ID**: {char.character_id}",
            f"**Session**: {char.session_id}",
            f"**Created**: {char.creation_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Images**: {char.total_images}",
            "",
            "**Image Breakdown**:",
            f"• Base Character: {'✓' if char.base_image_path and char.base_image_path.exists() else '✗'}",
            f"• Realistic Variations: {char.realistic_count}",
        ]
        
        if char.styled_counts:
            details.append("• Styled Images:")
            for style_name, count in char.styled_counts.items():
                details.append(f"  - {style_name}: {count}")
        
        if char.prompt:
            details.extend([
                "",
                "**Original Prompt**:",
                char.prompt[:200] + "..." if len(char.prompt) > 200 else char.prompt
            ])
        
        return "\n".join(details)
        
    except Exception as e:
        return f"Error loading character details: {str(e)}"

def format_character_grid_display(character_grid):
    """Format character grid for display in Gradio"""
    if not character_grid:
        return []
    
    display_items = []
    for char_data in character_grid:
        # Create display item with preview image and info
        preview_images = char_data.get("preview_images", [])
        if preview_images:
            image_path = preview_images[0][0]  # First preview image
        else:
            image_path = None
        
        # Create info text
        info_text = f"{char_data['character_id']} ({char_data['total_images']} images)"
        
        display_items.append({
            "image": image_path,
            "caption": info_text,
            "data": char_data
        })
    
    return display_items

# Build the Gradio interface
with gr.Blocks(theme=seafoam_theme, title=UI_CONFIG["title"]) as app:
    
    # Header
    gr.Markdown(f"# {UI_CONFIG['title']}")
    gr.Markdown(UI_CONFIG["description"])
    
    # API Setup Section
    with gr.Row():
        with gr.Column(scale=2):
            api_status = gr.Textbox(
                label="API Status", 
                interactive=False,
                value="Click 'Check API Setup' to validate your FAL API key",
                lines=3
            )
        with gr.Column(scale=1):
            check_api_btn = gr.Button("🔍 Check API Setup", variant="secondary")
            debug_mode = gr.Checkbox(label="🔧 Debug Mode", value=False, 
                                   info="Show detailed API logs and timing information")
    
    # Main Interface Tabs
    with gr.Tabs() as main_tabs:
        
        # Configuration Tab
        with gr.TabItem("⚙️ Configuration", id="config"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Character Details")
                    with gr.Group():
                        ethnicity = gr.Dropdown(
                            choices=CHARACTER_ETHNICITIES,
                            label="Ethnicity",
                            value="Asian"
                        )
                        gender = gr.Dropdown(
                            choices=CHARACTER_GENDERS,
                            label="Gender", 
                            value="Female"
                        )
                        age_range = gr.Dropdown(
                            choices=AGE_RANGES,
                            label="Age Range",
                            value="18-25"
                        )
                
                with gr.Column():
                    gr.Markdown("### Physical Features")
                    with gr.Group():
                        hair_color = gr.Dropdown(
                            choices=HAIR_COLORS,
                            label="Hair Color",
                            value="Black"
                        )
                        eye_color = gr.Dropdown(
                            choices=EYE_COLORS,
                            label="Eye Color", 
                            value="Brown"
                        )
                        build = gr.Dropdown(
                            choices=BUILD_TYPES,
                            label="Build",
                            value="Athletic"
                        )
                        height = gr.Dropdown(
                            choices=HEIGHT_TYPES,
                            label="Height",
                            value="Average"
                        )
            
            with gr.Row():
                with gr.Column():
                    clothing = gr.Dropdown(
                        choices=CLOTHING_STYLES,
                        label="Clothing Style",
                        value="Casual jeans and t-shirt"
                    )
                    facial_features = gr.Textbox(
                        label="Additional Facial Features (Optional)",
                        placeholder="e.g., friendly smile, expressive eyes",
                        lines=2
                    )
                
                with gr.Column():
                    gr.Markdown("### Session Settings")
                    with gr.Group():
                        session_id = gr.Textbox(
                            label="Session ID (Optional)",
                            placeholder="Auto-generated if empty",
                            value=""
                        )
                        character_id = gr.Textbox(
                            label="Character ID (Optional)", 
                            placeholder="Auto-generated if empty",
                            value=""
                        )
        
        # Generation Tab
        with gr.TabItem("🎨 Generate Base Character", id="generate"):
            with gr.Row():
                with gr.Column():
                    create_btn = gr.Button(
                        "🚀 Create Base Character", 
                        variant="primary",
                        size="lg"
                    )
                    generation_status = gr.Textbox(
                        label="Generation Status",
                        interactive=False,
                        lines=8,
                        max_lines=15,
                        autoscroll=True,
                        show_copy_button=True
                    )
                
                with gr.Column():
                    base_character_image = gr.Image(
                        label="Generated Base Character",
                        height=400
                    )
        
        # Variations Tab  
        with gr.TabItem("🔄 Consistency Variations", id="variations"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Test Prompts")
                    test_prompts = gr.Textbox(
                        label="Custom Test Prompts (one per line)",
                        placeholder="Leave empty to use default prompts",
                        lines=8,
                        value=""
                    )
                    
                    max_variations = gr.Slider(
                        minimum=1,
                        maximum=30,
                        value=10,
                        step=1,
                        label="Maximum Variations to Generate"
                    )
                    
                    generate_variations_btn = gr.Button(
                        "🔄 Generate Variations",
                        variant="primary"
                    )
                    
                    variations_status = gr.Textbox(
                        label="Variations Generation Status",
                        interactive=False,
                        lines=10,
                        max_lines=20,
                        autoscroll=True,
                        show_copy_button=True
                    )
                
                with gr.Column():
                    variations_gallery = gr.Gallery(
                        label="Generated Variations",
                        columns=3,
                        height=400
                    )
        
        # Styles Tab
        with gr.TabItem("🎭 Style Transfer", id="styles"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Available Styles")
                    
                    style_selector = gr.Radio(
                        choices=[(config["name"], key) for key, config in STYLE_CONFIGS.items()],
                        label="Select Style",
                        value="ghibli"
                    )
                    
                    # Style descriptions
                    for key, config in STYLE_CONFIGS.items():
                        gr.Markdown(f"**{config['name']}**: {config['description']}")
                    
                    apply_style_btn = gr.Button(
                        "🎨 Apply Style Transfer",
                        variant="primary"
                    )
                    
                    style_status = gr.Textbox(
                        label="Style Transfer Status",
                        interactive=False,
                        lines=10,
                        max_lines=20,
                        autoscroll=True,
                        show_copy_button=True
                    )
                
                with gr.Column():
                    styled_gallery = gr.Gallery(
                        label="Styled Images",
                        columns=3,
                        height=400
                    )
        
        # Gallery Tab
        with gr.TabItem("🖼️ Complete Gallery", id="gallery"):
            with gr.Row():
                with gr.Column(scale=1):
                    refresh_gallery_btn = gr.Button(
                        "🔄 Refresh Gallery",
                        variant="secondary"
                    )
                    session_summary = gr.Textbox(
                        label="Session Summary",
                        interactive=False,
                        lines=10
                    )
                
                with gr.Column(scale=3):
                    complete_gallery = gr.Gallery(
                        label="All Generated Images",
                        columns=4,
                        height=600
                    )
        
        # Character Library Tab
        with gr.TabItem("📚 Character Library", id="library"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📋 Character Management")
                    
                    # Refresh button
                    refresh_library_btn = gr.Button(
                        "🔄 Refresh Library",
                        variant="secondary"
                    )
                    
                    # Library status
                    library_status = gr.Textbox(
                        label="Library Status",
                        interactive=False,
                        lines=3
                    )
                    
                    # Download options
                    gr.Markdown("### 📥 Download Options")
                    include_metadata_check = gr.Checkbox(
                        label="Include Metadata Files",
                        value=True,
                        info="Include JSON metadata and generation parameters"
                    )
                    
                    # Individual download
                    download_single_btn = gr.Button(
                        "📦 Download Selected Character",
                        variant="primary"
                    )
                    
                    # Batch download (placeholder for future)
                    download_all_btn = gr.Button(
                        "📦 Download All Characters",
                        variant="secondary"
                    )
                    
                    # Download status
                    download_status = gr.Textbox(
                        label="Download Status",
                        interactive=False,
                        lines=5
                    )
                    
                    # Character details
                    gr.Markdown("### 📄 Character Details")
                    character_details = gr.Textbox(
                        label="Selected Character Info",
                        interactive=False,
                        lines=12
                    )
                
                with gr.Column(scale=3):
                    gr.Markdown("### 🎭 Character Collection")
                    
                    # Character grid/gallery
                    character_gallery = gr.Gallery(
                        label="Characters",
                        columns=3,
                        height=500,
                        object_fit="cover",
                        show_share_button=False
                    )
                    
                    # Selected character data (hidden)
                    selected_character_data = gr.State(value=None)
                    
                    # Character grid data (hidden)
                    character_grid_data = gr.State(value=[])
    
    # Event handlers
    check_api_btn.click(
        fn=validate_setup,
        outputs=api_status
    )
    
    debug_mode.change(
        fn=toggle_debug_mode,
        inputs=debug_mode,
        outputs=api_status
    )
    
    create_btn.click(
        fn=create_character,
        inputs=[
            ethnicity, gender, age_range, hair_color, eye_color,
            build, height, clothing, facial_features, session_id, character_id
        ],
        outputs=[generation_status, base_character_image, session_id]
    )
    
    generate_variations_btn.click(
        fn=generate_variations,
        inputs=[test_prompts, max_variations],
        outputs=[variations_status, variations_gallery]
    )
    
    apply_style_btn.click(
        fn=apply_style,
        inputs=[style_selector, variations_gallery],
        outputs=[style_status, styled_gallery]
    )
    
    refresh_gallery_btn.click(
        fn=refresh_gallery,
        outputs=complete_gallery
    )
    
    refresh_gallery_btn.click(
        fn=get_session_summary,
        outputs=session_summary
    )
    
    # Auto-refresh gallery when variations are generated
    generate_variations_btn.click(
        fn=refresh_gallery,
        outputs=complete_gallery
    )
    
    # Auto-refresh gallery when styles are applied
    apply_style_btn.click(
        fn=refresh_gallery,
        outputs=complete_gallery
    )
    
    # Character Library event handlers
    def handle_library_refresh():
        """Handle library refresh with proper return format"""
        character_grid, status_msg = refresh_character_library()
        
        # Format for gallery display
        gallery_items = []
        for char_data in character_grid:
            preview_images = char_data.get("preview_images", [])
            if preview_images:
                gallery_items.append(preview_images[0][0])  # First preview image path
        
        return gallery_items, status_msg, character_grid
    
    def handle_character_selection(evt: gr.SelectData, current_grid):
        """Handle character selection from gallery"""
        if evt.index is not None and current_grid:
            if 0 <= evt.index < len(current_grid):
                selected_char = current_grid[evt.index]
                details = get_character_details(selected_char)
                return selected_char, details
        return None, "No character selected"
    
    def handle_single_download(character_data, include_metadata):
        """Handle single character download"""
        if not character_data:
            return "❌ Please select a character first", None
        
        return download_character_zip(character_data, include_metadata)
    
    def handle_batch_download(character_grid, include_metadata):
        """Handle downloading all characters"""
        if not character_grid:
            return "❌ No characters available", None
        
        return download_batch_zip(character_grid, include_metadata)
    
    # Connect Character Library events
    refresh_library_btn.click(
        fn=handle_library_refresh,
        outputs=[character_gallery, library_status, character_grid_data]
    )
    
    character_gallery.select(
        fn=handle_character_selection,
        inputs=[character_grid_data],
        outputs=[selected_character_data, character_details]
    )
    
    download_single_btn.click(
        fn=handle_single_download,
        inputs=[selected_character_data, include_metadata_check],
        outputs=[download_status, gr.File()]
    )
    
    download_all_btn.click(
        fn=handle_batch_download,
        inputs=[character_grid_data, include_metadata_check],
        outputs=[download_status, gr.File()]
    )

# Launch the application
if __name__ == "__main__":
    print("🚀 Starting AI Character Creation Studio...")
    print("📋 Make sure to set your FAL_KEY environment variable")
    print("🌐 The application will be available at http://localhost:7860")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )