"""
GSC Coin Setup Script
Cross-platform setup for building executables
"""

import os
import sys
import subprocess
import platform

def install_dependencies():
    """Install required dependencies"""
    print("Installing GSC Coin dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_executable():
    """Build executable for current platform"""
    system = platform.system().lower()
    
    if system == "windows":
        build_windows()
    elif system == "darwin":  # macOS
        build_macos()
    elif system == "linux":
        build_linux()
    else:
        print(f"Unsupported platform: {system}")
        return False
    
    return True

def build_windows():
    """Build Windows executable"""
    print("Building Windows executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=GSCCoin",
        "--add-data=blockchain.py;.",
        "--add-data=wallet_manager.py;.",
        "--add-data=paper_wallet_generator.py;.",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=cryptography",
        "--hidden-import=PIL",
        "--hidden-import=qrcode",
        "launch_gsc_coin.py"
    ]
    
    subprocess.check_call(cmd)
    print("✓ Windows executable built: dist/GSCCoin.exe")

def build_macos():
    """Build macOS application"""
    print("Building macOS application...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=GSCCoin",
        "--add-data=blockchain.py:.",
        "--add-data=wallet_manager.py:.",
        "--add-data=paper_wallet_generator.py:.",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=cryptography",
        "--hidden-import=PIL",
        "--hidden-import=qrcode",
        "launch_gsc_coin.py"
    ]
    
    subprocess.check_call(cmd)
    print("✓ macOS application built: dist/GSCCoin.app")

def build_linux():
    """Build Linux executable"""
    print("Building Linux executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name=GSCCoin",
        "--add-data=blockchain.py:.",
        "--add-data=wallet_manager.py:.",
        "--add-data=paper_wallet_generator.py:.",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=cryptography",
        "--hidden-import=PIL",
        "--hidden-import=qrcode",
        "launch_gsc_coin.py"
    ]
    
    subprocess.check_call(cmd)
    print("✓ Linux executable built: dist/GSCCoin")

def main():
    """Main setup function"""
    print("GSC Coin Cross-Platform Setup")
    print("=" * 40)
    
    # Install dependencies
    try:
        install_dependencies()
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    
    # Build executable
    try:
        if build_executable():
            print("\n" + "=" * 40)
            print("✓ GSC Coin build completed successfully!")
            print(f"Platform: {platform.system()}")
            print("Check the 'dist' folder for your executable.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build executable: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
