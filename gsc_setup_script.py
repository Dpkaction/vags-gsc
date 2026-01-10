
import os
import sys
import tempfile
import zipfile
import subprocess
import shutil
from pathlib import Path

def extract_and_run():
    """Extract files and run installer"""
    try:
        # Get the directory where this exe is located
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix='gsc_installer_')
        
        # Extract embedded files (this would be replaced with actual embedded data)
        installer_files = {
            'GSC_Coin_Wallet.exe': 'GSC_Coin_Wallet.exe',
            'README.txt': 'README.txt', 
            'LICENSE.txt': 'LICENSE.txt',
            'install.bat': 'install.bat'
        }
        
        # Copy files to temp directory (in real implementation, these would be embedded)
        for src, dst in installer_files.items():
            src_path = os.path.join(exe_dir, src)
            if os.path.exists(src_path):
                shutil.copy2(src_path, os.path.join(temp_dir, dst))
        
        # Run the installer
        install_script = os.path.join(temp_dir, 'install.bat')
        if os.path.exists(install_script):
            subprocess.run([install_script], cwd=temp_dir, shell=True)
        
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
            
    except Exception as e:
        print(f"Installation failed: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    extract_and_run()
