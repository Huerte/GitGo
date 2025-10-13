from utils.colors import *
from pathlib import Path
import shutil
import sys
import os


def clean_project(arguments):
    if len(arguments) > 1:
        if arguments[1] in ("-h", "--help", "help"):
            print("\nUsage: gitgo clean\n")
            print("This helps to free up space and remove unnecessary files from the project.\n")
            print("\nSyntax:\n")
            print("        gitgo clean               # Cleans the project by removing build directories and temporary files\n")
            sys.exit(0)

        error("\nToo many arguments for clean operation!\n")
        sys.exit(1)

    proceed = False

    info("\nThis will remove build directories and temporary files from the project.")
    info("Are you sure you want to proceed? (y/n): ")
    while not proceed:
        confirm = input(">> ").strip().lower()
        if confirm.lower() == 'y':
            proceed = True
        elif confirm == 'n':
            warning("\nClean operation cancelled by user.\n")
            sys.exit(0)
        else:
            error("\nInvalid input. Please enter 'y' or 'n'.\n")
    
    # List of common build directories to clean
    BUILD_DIRS = ['build', 'dist', '__pycache__', '.pytest_cache', '.mypy_cache', '.venv', 'env', '.env']
    FILE_PATTERNS = ['*.pyc', '*.pyo', '*~', '*.log']

    # Current working directory
    base_path = Path.cwd()

    # Remove build directories
    # `topdown=False` to ensure we delete subdirectories before their parents
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            if dir_name in BUILD_DIRS:
                dir_path = Path(root) / dir_name
                try:
                    shutil.rmtree(dir_path)
                    success(f"Removed directory: {dir_path}")
                except Exception as e:
                    error(f"Failed to remove directory {dir_path}: {e}")
        
        for pattern in FILE_PATTERNS:
            for file_name in files:
                if file_name.endswith(pattern.replace("*", "")):
                    file_path = Path(root) / file_name
                    try:
                        file_path.unlink()
                        success(f"Removed file: {file_path}")
                    except Exception as e:
                        error(f"Failed to remove file {file_path}: {e}")
    
    info("\nProject cleaned successfully.\n")

