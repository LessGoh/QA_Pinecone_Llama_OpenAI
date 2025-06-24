"""
Main application entry point for QA Bot - Streamlit only version.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.database.database import create_tables


def run_streamlit():
    """Run the Streamlit web application."""
    import subprocess
    subprocess.run([
        "streamlit", "run", 
        "src/ui/streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])


def init_database():
    """Initialize the database."""
    print("Initializing database...")
    create_tables()
    print("Database initialized successfully!")


def main():
    """Main function to run Streamlit app."""
    print("Starting QA Bot - Streamlit Application...")
    init_database()
    run_streamlit()


if __name__ == "__main__":
    main()