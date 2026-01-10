import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from wallet_manager import WalletManager
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageTk
from datetime import datetime
import os

class PaperWalletGenerator:
    """Professional paper wallet generator for GSC Coin"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.wallet_manager = WalletManager()
        
    def show_paper_wallet_dialog(self):
        """Show paper wallet generation dialog"""
        dialog = tk.Toplevel(self.parent if self.parent else tk.Tk())
        dialog.title("Generate Paper Wallet")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        
        # Title
        title_label = ttk.Label(dialog, text="GSC Coin Paper Wallet Generator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Instructions
        instructions = ttk.Label(dialog, text="Generate a secure paper wallet for offline GSC coin storage.\n"
                                            "Keep your private key safe and never share it with anyone!",
                                font=("Arial", 10))
        instructions.pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(dialog, text="Paper Wallet Options", padding=15)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Number of wallets
        ttk.Label(options_frame, text="Number of wallets to generate:").grid(row=0, column=0, sticky=tk.W, pady=5)
        wallet_count_var = tk.StringVar(value="1")
        wallet_count_spin = ttk.Spinbox(options_frame, from_=1, to=10, textvariable=wallet_count_var, width=10)
        wallet_count_spin.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Include QR codes
        qr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include QR codes", variable=qr_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # High security mode
        secure_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="High security mode (longer keys)", variable=secure_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(dialog, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Preview canvas
        preview_canvas = tk.Canvas(preview_frame, width=500, height=200, bg='white', relief=tk.SUNKEN, bd=2)
        preview_canvas.pack(pady=10)
        
        # Draw sample preview
        preview_canvas.create_text(250, 30, text="GSC Coin Paper Wallet", font=("Arial", 14, "bold"))
        preview_canvas.create_text(250, 60, text="Public Address: GSC1a2b3c4d5e6f7g8h9i0j...", font=("Arial", 10))
        preview_canvas.create_text(250, 90, text="Private Key: [HIDDEN - Will be shown on actual wallet]", font=("Arial", 10))
        preview_canvas.create_rectangle(50, 110, 150, 180, outline="black")
        preview_canvas.create_text(100, 145, text="Address\nQR Code", font=("Arial", 8))
        preview_canvas.create_rectangle(350, 110, 450, 180, outline="black")
        preview_canvas.create_text(400, 145, text="Private Key\nQR Code", font=("Arial", 8))
        
        # Buttons frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def generate_paper_wallets():
            """Generate paper wallets"""
            try:
                count = int(wallet_count_var.get())
                include_qr = qr_var.get()
                high_security = secure_var.get()
                
                # Ask for save location
                save_dir = filedialog.askdirectory(title="Select folder to save paper wallets")
                if not save_dir:
                    return
                
                generated_wallets = []
                
                for i in range(count):
                    # Generate wallet data
                    address, private_key = self.wallet_manager.generate_address()
                    
                    # Create paper wallet image
                    wallet_image = self.create_paper_wallet_image(
                        address, private_key, include_qr, high_security, i + 1
                    )
                    
                    # Save wallet
                    filename = f"GSC_Paper_Wallet_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    filepath = os.path.join(save_dir, filename)
                    wallet_image.save(filepath)
                    
                    generated_wallets.append({
                        'address': address,
                        'private_key': private_key,
                        'filename': filename
                    })
                
                # Show success message
                success_msg = f"Successfully generated {count} paper wallet(s)!\n\n"
                success_msg += f"Saved to: {save_dir}\n\n"
                success_msg += "IMPORTANT SECURITY NOTES:\n"
                success_msg += "• Print these wallets and store them securely\n"
                success_msg += "• Never share your private keys\n"
                success_msg += "• Keep multiple copies in safe locations\n"
                success_msg += "• Delete digital copies after printing"
                
                messagebox.showinfo("Paper Wallets Generated", success_msg)
                
                # Show wallet details
                self.show_wallet_details(generated_wallets)
                
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate paper wallets: {str(e)}")
        
        ttk.Button(button_frame, text="Generate Paper Wallets", 
                  command=generate_paper_wallets).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        if not self.parent:
            dialog.mainloop()
    
    def create_paper_wallet_image(self, address, private_key, include_qr=True, high_security=False, wallet_num=1):
        """Create paper wallet image"""
        # Image dimensions
        width, height = 800, 600
        
        # Create image
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            header_font = ImageFont.truetype("arial.ttf", 14)
            text_font = ImageFont.truetype("arial.ttf", 12)
            small_font = ImageFont.truetype("arial.ttf", 10)
            code_font = ImageFont.truetype("courier.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            code_font = ImageFont.load_default()
        
        # Draw border
        draw.rectangle([10, 10, width-10, height-10], outline="black", width=3)
        draw.rectangle([20, 20, width-20, height-20], outline="gray", width=1)
        
        # Title
        title_text = f"GSC Coin Paper Wallet #{wallet_num}"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 40), title_text, fill="black", font=title_font)
        
        # Subtitle
        subtitle = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=small_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((width - subtitle_width) // 2, 75), subtitle, fill="gray", font=small_font)
        
        # Security warning
        warning_text = "⚠️ KEEP PRIVATE KEY SECRET - NEVER SHARE OR PHOTOGRAPH ⚠️"
        warning_bbox = draw.textbbox((0, 0), warning_text, font=header_font)
        warning_width = warning_bbox[2] - warning_bbox[0]
        draw.text(((width - warning_width) // 2, 100), warning_text, fill="red", font=header_font)
        
        # Public Address Section
        draw.text((50, 150), "PUBLIC ADDRESS (Share this to receive GSC coins):", fill="green", font=header_font)
        
        # Split address into multiple lines if too long
        addr_lines = [address[i:i+50] for i in range(0, len(address), 50)]
        y_pos = 175
        for line in addr_lines:
            draw.text((50, y_pos), line, fill="black", font=code_font)
            y_pos += 20
        
        # Private Key Section
        draw.text((50, 280), "PRIVATE KEY (Keep this secret!):", fill="red", font=header_font)
        
        # Split private key into multiple lines
        key_lines = [private_key[i:i+50] for i in range(0, len(private_key), 50)]
        y_pos = 305
        for line in key_lines:
            draw.text((50, y_pos), line, fill="red", font=code_font)
            y_pos += 20
        
        # QR Codes
        if include_qr:
            try:
                # Address QR Code
                addr_qr = qrcode.QRCode(version=1, box_size=4, border=2)
                addr_qr.add_data(address)
                addr_qr.make(fit=True)
                addr_qr_img = addr_qr.make_image(fill_color="black", back_color="white")
                addr_qr_img = addr_qr_img.resize((120, 120))
                img.paste(addr_qr_img, (550, 140))
                
                draw.text((580, 270), "Address QR", fill="black", font=small_font)
                
                # Private Key QR Code
                key_qr = qrcode.QRCode(version=1, box_size=4, border=2)
                key_qr.add_data(private_key)
                key_qr.make(fit=True)
                key_qr_img = key_qr.make_image(fill_color="black", back_color="white")
                key_qr_img = key_qr_img.resize((120, 120))
                img.paste(key_qr_img, (550, 300))
                
                draw.text((570, 430), "Private Key QR", fill="red", font=small_font)
                
            except Exception as e:
                print(f"QR code generation failed: {e}")
        
        # Instructions
        instructions = [
            "INSTRUCTIONS:",
            "1. Print this wallet and store it securely",
            "2. Send GSC coins to the public address above",
            "3. To spend coins, import the private key into your wallet",
            "4. Never share or photograph the private key",
            "5. Keep multiple copies in different safe locations"
        ]
        
        y_pos = 480
        for instruction in instructions:
            color = "black" if instruction.startswith("INSTRUCTIONS") else "darkblue"
            font = header_font if instruction.startswith("INSTRUCTIONS") else small_font
            draw.text((50, y_pos), instruction, fill=color, font=font)
            y_pos += 15
        
        # Footer
        footer_text = "GSC Coin - Secure Cryptocurrency Storage"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(((width - footer_width) // 2, height - 30), footer_text, fill="gray", font=small_font)
        
        return img
    
    def show_wallet_details(self, wallets):
        """Show generated wallet details"""
        details_window = tk.Toplevel(self.parent if self.parent else tk.Tk())
        details_window.title("Generated Paper Wallets")
        details_window.geometry("700x500")
        
        # Title
        ttk.Label(details_window, text="Generated Paper Wallets", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        # Warning
        warning_frame = ttk.Frame(details_window)
        warning_frame.pack(fill=tk.X, padx=20, pady=10)
        
        warning_text = ("⚠️ SECURITY WARNING ⚠️\n"
                       "The private keys below are shown for verification only.\n"
                       "Delete this information after printing your paper wallets!")
        
        warning_label = ttk.Label(warning_frame, text=warning_text, 
                                 foreground="red", font=("Arial", 10, "bold"))
        warning_label.pack()
        
        # Wallet details
        details_frame = ttk.LabelFrame(details_window, text="Wallet Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview
        tree = ttk.Treeview(details_frame, columns=("Address", "Private Key", "File"), show="headings")
        tree.heading("#1", text="Public Address")
        tree.heading("#2", text="Private Key")
        tree.heading("#3", text="Filename")
        
        # Configure column widths
        tree.column("#1", width=200)
        tree.column("#2", width=200)
        tree.column("#3", width=200)
        
        # Add wallet data
        for wallet in wallets:
            tree.insert("", tk.END, values=(
                wallet['address'][:30] + "...",
                wallet['private_key'][:30] + "...",
                wallet['filename']
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(details_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def copy_address():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                wallet_idx = tree.index(selection[0])
                address = wallets[wallet_idx]['address']
                details_window.clipboard_clear()
                details_window.clipboard_append(address)
                messagebox.showinfo("Copied", "Address copied to clipboard")
        
        ttk.Button(button_frame, text="Copy Selected Address", 
                  command=copy_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=details_window.destroy).pack(side=tk.RIGHT, padx=5)

if __name__ == "__main__":
    # Standalone paper wallet generator
    generator = PaperWalletGenerator()
    generator.show_paper_wallet_dialog()
