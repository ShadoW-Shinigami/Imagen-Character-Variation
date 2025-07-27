# 🎨 AI Character Creation Studio

A modern, user-friendly Gradio interface for creating consistent character images using Imagen 4, Kontext Max, and LoRA style transfers.

## ✨ Features

- **🎯 Character Configuration**: Interactive form for detailed character customization
- **🖼️ Base Character Generation**: Create initial character using Imagen 4
- **🔄 Consistency Variations**: Generate multiple poses and expressions with Kontext Max
- **🎭 Style Transfer**: Apply Studio Ghibli and Rick & Morty styles using LoRA
- **📚 Character Library**: Browse, manage, and download all created characters
- **📦 ZIP Export**: Download characters with images, metadata, and generation parameters
- **📱 Modern UI**: Clean, responsive interface with custom Seafoam theme
- **📊 Session Management**: Organized output with progress tracking

## 🚀 Quick Start

### Prerequisites

1. **FAL API Key**: Get your API key from [FAL AI](https://fal.ai)
2. **Python 3.8+**: Make sure you have Python installed

### Installation

1. **Clone or download** this repository
2. **Navigate to the app directory**:
   ```bash
   cd app
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your API key** (Choose one method):

   **Method 1 - .env File (Recommended):**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and replace with your actual API key
   # FAL_KEY=your_actual_api_key_here
   ```

   **Method 2 - Environment Variables:**
   ```bash
   # Windows (Command Prompt)
   set FAL_KEY=your_api_key_here
   
   # Windows (PowerShell)  
   $env:FAL_KEY="your_api_key_here"
   
   # Mac/Linux
   export FAL_KEY=your_api_key_here
   ```

   Get your API key from: https://fal.ai/dashboard

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Open your browser** to `http://localhost:7860`

## 🎯 How to Use

### 1. **API Setup**
- Click "Check API Setup" to validate your FAL API key
- Ensure you see a green checkmark before proceeding

### 2. **Configure Character**
- Fill in character details (ethnicity, gender, age, etc.)
- Customize physical features and clothing
- Add optional facial features description

### 3. **Generate Base Character**
- Click "Create Base Character" to generate the initial image
- Wait for generation to complete (usually 30-60 seconds)

### 4. **Create Variations**
- Use default prompts or add custom ones (one per line)
- Set maximum number of variations to generate
- Click "Generate Variations" to create consistency tests

### 5. **Apply Styles**
- Choose between Studio Ghibli or Rick & Morty styles
- Click "Apply Style Transfer" to transform your variations
- View results in the styled gallery

### 6. **View Complete Gallery**
- Check the "Complete Gallery" tab for all generated images
- Use "Refresh Gallery" to update the view
- Review session summary for statistics

### 7. **Character Library & Downloads**
- Visit the "Character Library" tab to browse all created characters
- Click on any character to view detailed information
- Download individual characters or all characters as ZIP files
- ZIP exports include images, metadata, and generation parameters

## 📁 Output Structure

```
Session_YYYYMMDD_HHMMSS/
├── Character_HHMMSS/
│   ├── Base-Character.png
│   ├── base_character_metadata.json
│   ├── ConsistencyTests/
│   │   ├── Realistic_001.png
│   │   ├── Realistic_002.png
│   │   └── ...
│   └── Styles/
│       ├── Studio Ghibli/
│       │   ├── Studio Ghibli_001.png
│       │   └── ...
│       └── Rick & Morty/
│           ├── Rick & Morty_001.png
│           └── ...
```

## ⚙️ Configuration

### Character Options
- **Ethnicities**: Asian, Caucasian, African, Hispanic, Middle Eastern, Native American, Mixed
- **Age Ranges**: 18-25, 26-35, 36-45, 46-55, 56-65, 65+
- **Physical Features**: Hair color, eye color, build type, height
- **Clothing Styles**: Casual, business, formal, sporty, elegant, bohemian, vintage, streetwear

### API Parameters
All API parameters are pre-configured for optimal results but can be customized in `config.py`:
- **Imagen 4**: Aspect ratio, image count, negative prompts
- **Kontext Max**: Guidance scale, safety tolerance, output format  
- **Kontext LoRA**: Inference steps, LoRA weights, acceleration

## 🛠️ Technical Details

### Architecture
- **`app.py`**: Main Gradio interface with custom Seafoam theme
- **`character_creator.py`**: Core generation logic and workflow management
- **`utils.py`**: Helper functions for API calls and image handling
- **`config.py`**: Configuration constants and parameters
- **`.env`**: Environment variables (API keys) - create from `.env.example`

### Key Features
- **Progressive Generation**: Step-by-step workflow with progress tracking
- **Error Handling**: Graceful failure recovery and user feedback
- **Session Management**: Organized file structure and metadata tracking
- **Modern UI**: Responsive design with grouped components and clean layout

## 🔧 Troubleshooting

### Common Issues

**"API key not found"**
- **Using .env file**: Make sure you've copied `.env.example` to `.env` and added your actual API key
- **Using environment variables**: Make sure you've set the `FAL_KEY` environment variable
- Restart your terminal/command prompt after setting environment variables
- Check that your `.env` file is in the same directory as `app.py`

**"Generation failed"**
- Check your internet connection
- Verify your API key is valid and has sufficient credits
- Try reducing the number of variations if hitting rate limits

**"No images generated"**
- Ensure all required character fields are filled
- Check the generation status messages for specific errors
- Try simplifying your prompts if using custom ones

### Performance Tips
- Start with fewer variations (5-10) to test the workflow
- Generate styles for smaller batches to avoid timeouts
- Use shorter, simpler custom prompts for better results

## 📞 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your API key and internet connection  
3. Try with default settings first
4. Reduce batch sizes if experiencing timeouts

## 🚨 Important Notes

- **API Costs**: Each generation consumes API credits
- **Processing Time**: Generation can take 1-3 minutes per batch
- **File Management**: Check output folders for organized results
- **Memory Usage**: Large batches may require significant RAM

## 🎉 Enjoy Creating!

This tool combines the power of modern AI image generation with an intuitive interface. Create consistent, high-quality character variations for your projects, games, stories, or creative endeavors!