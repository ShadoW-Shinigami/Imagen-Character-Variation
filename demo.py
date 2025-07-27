#!/usr/bin/env python3
"""
Demo script to showcase the Character Creation Studio interface

This script demonstrates the UI components without requiring API calls.
"""

import gradio as gr
from app import SeafoamTheme
from config import CHARACTER_ETHNICITIES, CHARACTER_GENDERS, HAIR_COLORS, EYE_COLORS

def demo_character_prompt(ethnicity, gender, age_range, hair_color, eye_color, 
                         build, height, clothing, facial_features):
    """Demo function to show character prompt generation"""
    prompt_parts = [
        f"Professional photograph of a {age_range}-year-old {ethnicity} {gender.lower()}",
        f"with {hair_color.lower()} hair and {eye_color.lower()} eyes",
        f"{build.lower()} build, {height.lower()} height",
        f"wearing {clothing}"
    ]
    
    if facial_features:
        prompt_parts.append(f"with {facial_features}")
    
    prompt_parts.extend([
        "full body image",
        "plain white background", 
        "professional studio lighting",
        "high quality, detailed, realistic"
    ])
    
    return ", ".join(prompt_parts)

# Create demo interface with simplified functionality
with gr.Blocks(theme=SeafoamTheme(), title="Character Creation Studio - Demo") as demo:
    
    gr.Markdown("# 🎨 AI Character Creation Studio - Demo Mode")
    gr.Markdown("This demo shows the interface without making actual API calls.")
    
    with gr.Tabs():
        with gr.TabItem("Character Configuration"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Character Details")
                    ethnicity = gr.Dropdown(choices=CHARACTER_ETHNICITIES, label="Ethnicity", value="Asian")
                    gender = gr.Dropdown(choices=CHARACTER_GENDERS, label="Gender", value="Female")
                    age_range = gr.Dropdown(choices=["18-25", "26-35", "36-45"], label="Age Range", value="18-25")
                
                with gr.Column():
                    gr.Markdown("### Physical Features")
                    hair_color = gr.Dropdown(choices=HAIR_COLORS, label="Hair Color", value="Black")
                    eye_color = gr.Dropdown(choices=EYE_COLORS, label="Eye Color", value="Brown")
                    build = gr.Dropdown(choices=["Slim", "Athletic", "Average"], label="Build", value="Athletic")
                    height = gr.Dropdown(choices=["Short", "Average", "Tall"], label="Height", value="Average")
            
            with gr.Row():
                clothing = gr.Textbox(label="Clothing", value="Casual jeans and white t-shirt")
                facial_features = gr.Textbox(label="Facial Features (Optional)", 
                                           placeholder="e.g., friendly smile, expressive eyes")
            
            generate_prompt_btn = gr.Button("Generate Character Prompt", variant="primary")
            character_prompt = gr.Textbox(label="Generated Prompt", lines=4, interactive=False)
        
        with gr.TabItem("Sample Gallery"):
            gr.Markdown("### This is where your generated images would appear")
            sample_gallery = gr.Gallery(
                label="Generated Images", 
                columns=3,
                height=400,
                value=[]
            )
            gr.Markdown("*Images will appear here after generation*")
    
    # Connect the demo function
    generate_prompt_btn.click(
        fn=demo_character_prompt,
        inputs=[ethnicity, gender, age_range, hair_color, eye_color, 
                build, height, clothing, facial_features],
        outputs=character_prompt
    )

if __name__ == "__main__":
    print("🎨 Character Creation Studio - Demo Mode")
    print("This demo shows the interface without API calls")
    print("Access at: http://localhost:7861")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False
    )