#!/usr/bin/env python3
"""
Founder Intelligence App Launcher
Simple launcher that runs the Streamlit UI.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app_streamlit.py"
    ])

if __name__ == "__main__":
    main() 