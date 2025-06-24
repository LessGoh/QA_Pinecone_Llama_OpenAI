"""
Main application entry point for QA Bot - Streamlit Cloud version.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database.database import create_tables

# Initialize database on startup (optional for Streamlit Cloud)
try:
    create_tables()
except Exception as e:
    print(f"Database initialization skipped: {e}")

# Import and run the main Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()