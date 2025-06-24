#!/usr/bin/env python3
"""
Streamlit application runner with proper configuration.
"""
import os
import sys
from pathlib import Path

# Ensure proper module path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for Streamlit
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')

if __name__ == "__main__":
    # Import and run Streamlit
    import streamlit.web.cli as stcli
    import streamlit as st
    
    # Set the main script
    main_script = str(project_root / "src" / "ui" / "streamlit_app.py")
    
    # Run Streamlit
    sys.argv = [
        "streamlit",
        "run",
        main_script,
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    stcli.main()