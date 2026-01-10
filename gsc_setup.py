import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import shutil
import subprocess

class GSCSetup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GSC Coin Setup")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        try:
            self.root.iconbitmap("gsc_icon.ico")
        except:
            pass
        
        self.install_path = "C:\\Program Files\\GSC Coin"
        self.create_gui()
        
    def create_gui(self):
        # Header
        header = tk.Frame(self.root, bg='white', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="GSC Coin", font=("Arial", 24, "bold"), 
                bg='white', fg='#2e7d32').pack(pady=20)
        
        # Main content
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        welcome = """Welcome to GSC Coin Setup

This will install GSC Coin 2.0 on your computer.

GSC Coin features:
• Professional cryptocurrency wallet
• 21.75 trillion GSC total supply
• Bitcoin-like mining system
• Advanced security features
• QR code generation"""
        
        tk.Label(main, text=welcome, justify=tk.LEFT, font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 20))
        
        # Install path
        path_frame = tk.Frame(main)
        path_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(path_frame, text="Installation folder:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.path_entry = tk.Entry(path_frame, font=("Arial", 10))
        self.path_entry.insert(0, self.install_path)
        self.path_entry.pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(main)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        tk.Button(btn_frame, text="Cancel", command=self.root.quit, width=12).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(btn_frame, text="Install", command=self.install, width=12, 
                 bg='#2e7d32', fg='white', font=("Arial", 10, "bold")).pack(side=tk.RIGHT)
        
    def install(self):
        self.install_path = self.path_entry.get()
        
        # Progress window
        progress = tk.Toplevel(self.root)
        progress.title("Installing GSC Coin")
        progress.geometry("400x150")
        progress.resizable(False, False)
        progress.transient(self.root)
        progress.grab_set()
        
        tk.Label(progress, text="Installing GSC Coin...", font=("Arial", 12, "bold")).pack(pady=20)
        
        pbar = ttk.Progressbar(progress, mode='indeterminate')
        pbar.pack(pady=10, padx=40, fill=tk.X)
        pbar.start()
        
        status = tk.Label(progress, text="Installing files...", font=("Arial", 10))
        status.pack(pady=10)
        
        self.root.after(100, lambda: self.do_install(progress, pbar))
        
    def do_install(self, progress, pbar):
        try:
            # Create directory
            os.makedirs(self.install_path, exist_ok=True)
            
            # Find GSCCoin.exe (it's bundled with the installer)
            exe_source = None
            possible_locations = [
                "GSCCoin.exe",  # Current directory
                os.path.join(sys._MEIPASS, "GSCCoin.exe") if hasattr(sys, '_MEIPASS') else None,  # PyInstaller bundle
                os.path.join(os.path.dirname(sys.executable), "GSCCoin.exe"),  # Same directory as installer
            ]
            
            for location in possible_locations:
                if location and os.path.exists(location):
                    exe_source = location
                    break
            
            if not exe_source:
                raise Exception("GSCCoin.exe not found. Please ensure the installer contains the GSC Coin executable.")
            
            # Copy executable
            exe_dest = os.path.join(self.install_path, "GSCCoin.exe")
            shutil.copy2(exe_source, exe_dest)
            
            # Verify the copy was successful
            if not os.path.exists(exe_dest):
                raise Exception("Failed to copy GSCCoin.exe to installation directory.")
            
            # Create shortcuts
            self.create_shortcuts()
            
            pbar.stop()
            progress.destroy()
            
            # Success
            messagebox.showinfo("Success", "GSC Coin installed successfully!\n\nLocation: " + self.install_path + "\n\nDesktop shortcut created.")
            self.root.quit()
            
        except Exception as e:
            pbar.stop()
            progress.destroy()
            messagebox.showerror("Installation Error", "Installation failed:\n\n" + str(e) + "\n\nPlease try running as administrator or choose a different installation folder.")
    
    def create_shortcuts(self):
        try:
            exe_path = os.path.join(self.install_path, "GSCCoin.exe")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut = os.path.join(desktop, "GSC Coin.lnk")
            
            # Create PowerShell command to create shortcut
            ps_cmd = [
                "powershell", "-Command",
                "$WshShell = New-Object -comObject WScript.Shell; " +
                "$Shortcut = $WshShell.CreateShortcut('" + shortcut + "'); " +
                "$Shortcut.TargetPath = '" + exe_path + "'; " +
                "$Shortcut.Description = 'GSC Coin - Professional Cryptocurrency Wallet'; " +
                "$Shortcut.Save()"
            ]
            
            subprocess.run(ps_cmd, capture_output=True, shell=False)
        except:
            pass  # Shortcut creation is optional
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    GSCSetup().run()
