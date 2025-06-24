"""
Main application entry point for QA Bot.
"""
import argparse
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


def run_fastapi():
    """Run the FastAPI REST API."""
    import uvicorn
    uvicorn.run(
        "src.api.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


def init_database():
    """Initialize the database."""
    print("Initializing database...")
    create_tables()
    print("Database initialized successfully!")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="QA Bot Application")
    parser.add_argument(
        "mode",
        choices=["streamlit", "fastapi", "init-db"],
        help="Application mode to run"
    )
    
    args = parser.parse_args()
    
    if args.mode == "streamlit":
        print("Starting Streamlit web application...")
        run_streamlit()
    elif args.mode == "fastapi":
        print("Starting FastAPI REST API...")
        run_fastapi()
    elif args.mode == "init-db":
        init_database()


if __name__ == "__main__":
    main()