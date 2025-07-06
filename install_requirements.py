import subprocess
import sys
import os

REQUIREMENTS = 'requirements.txt'

def main():
    if not os.path.exists(REQUIREMENTS):
        print(f"[ERROR] {REQUIREMENTS} not found in the current directory.")
        sys.exit(1)
    print(f"[INFO] Installing dependencies from {REQUIREMENTS}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', REQUIREMENTS])
        print("[INFO] All dependencies installed successfully!")
    except FileNotFoundError:
        print("[ERROR] pip is not installed or not found in your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 