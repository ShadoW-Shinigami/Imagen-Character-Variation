#!/usr/bin/env python3
"""
Launch script for AI Character Creation Studio

This script provides a simple way to start the application with proper error handling.
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly set up"""
    print("Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check required modules
    required_modules = ['gradio', 'fal_client', 'requests', 'PIL', 'matplotlib']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"OK: {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"ERROR: {module}")
    
    if missing_modules:
        print(f"\nERROR: Missing modules: {', '.join(missing_modules)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    # Check API key
    if 'FAL_KEY' not in os.environ:
        env_file_exists = Path('.env').exists()
        env_example_exists = Path('.env.example').exists()
        
        print("\nWARNING: FAL_KEY not found")
        
        if env_example_exists and not env_file_exists:
            print("SOLUTION: Copy .env.example to .env and add your API key")
            print("  1. cp .env.example .env")
            print("  2. Edit .env and replace placeholder with actual key")
        elif env_file_exists:
            print("SOLUTION: Add FAL_KEY to your .env file")
            print("  Add line: FAL_KEY=your_api_key_here")
        else:
            print("SOLUTION: Create .env file or set environment variable")
            print("  Option 1: Create .env with: FAL_KEY=your_api_key_here")
            print("  Option 2: export FAL_KEY=your_api_key_here")
        
        print("Get your API key from: https://fal.ai/dashboard")
        print("The application will still launch but won't work without an API key")
    else:
        print("OK: FAL_KEY found")
    
    return True

def main():
    """Main launch function"""
    print("AI Character Creation Studio")
    print("="*50)
    
    if not check_environment():
        print("\nEnvironment check failed. Please fix the issues above.")
        sys.exit(1)
    
    print("\nStarting application...")
    print("Make sure your FAL API key is set in the environment")
    print("The application will be available at http://localhost:7860")
    print("Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Import and launch the app
        from app import app
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            show_api=False
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"\nError starting application: {e}")
        print("Please check the error message above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()