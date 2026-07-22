import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent # Paths in this folder we are using
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
MAIN_FILE = PROJECT_ROOT / "main.py" #THIS IS THE MAIN FILE THAT WILL BE USED TO START THE APPLICATION

MARKER_FILE = VENV_DIR / "requirements_installed" #used to check if the requirements were installed already

def create_venv():
    print("Checking virtual environment...")
    if VENV_DIR.exists():
        print("Virtual environment exists")
        return
    
    print("Creating virtual environment")
    subprocess.check_call([sys.executable,"-m","venv",str(VENV_DIR)])
    print("Virtual environment created")



def get_venv_python():
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"



def install_requirements(): # Install requirements to python environment
    python = get_venv_python()

    print("Installing dependencies...")

    print("Updating pip")
    subprocess.check_call([str(python),"-m","pip","install","--upgrade","pip"]) #Update current pip

    print("Installing requirements")
    subprocess.check_call([str(python),"-m","pip","install","-r",str(REQUIREMENTS)]) #installs all requirements

    print("Dependencies installed")
    MARKER_FILE.touch() #create marker file, used to check later

def launch():
    python = get_venv_python()

    print("Launching application...")
    subprocess.call([str(python),str(MAIN_FILE)]) #Start the application



def requirements_need_installing():
    if not MARKER_FILE.exists():# Has it been installed already
        return True

    if not REQUIREMENTS.exists(): #Does the requirements file exist
        print("requirements.txt not found.")
        return False
    
    return REQUIREMENTS.stat().st_mtime > MARKER_FILE.stat().st_mtime #Check if the requirements.txt has changed



def main():
    try:
        print(f"Using Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        create_venv()

        

    except subprocess.CalledProcessError as e:
        print(f"Bootstrap failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()