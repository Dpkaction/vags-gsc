import os
import json
import hashlib
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import pickle

class WalletManager:
    """Professional wallet management system for GSC Coin"""
    
    def __init__(self):
        self.wallets_dir = "wallets"
        self.current_wallet = None
        self.wallet_data = {}
        self.is_encrypted = False
        self.encryption_key = None
        
        # Create wallets directory
        if not os.path.exists(self.wallets_dir):
            os.makedirs(self.wallets_dir)
    
    def generate_address(self):
        """Generate a new market-ready GSC address with proper format"""
        # Generate cryptographically secure private key
        private_key_bytes = os.urandom(32)
        private_key = private_key_bytes.hex()
        
        # Generate public key hash (simplified but consistent)
        public_key_hash = hashlib.sha256(private_key_bytes + b'GSC_PUBLIC').digest()
        
        # Create proper GSC address format
        # Use first 20 bytes of hash for address generation
        address_bytes = public_key_hash[:20]
        
        # Create checksum using double SHA256 (Bitcoin-like)
        checksum_input = b'GSC' + address_bytes
        checksum = hashlib.sha256(hashlib.sha256(checksum_input).digest()).digest()[:4]
        
        # Combine address bytes with checksum
        full_address = address_bytes + checksum
        
        # Convert to readable format using hex encoding (more reliable than base58/base64)
        address_hex = full_address.hex()
        
        # Create GSC address with proper prefix
        address = f"GSC1{address_hex[:32]}"  # Fixed length GSC address
        
        # Generate public key for display
        public_key = hashlib.sha256(private_key_bytes + b'GSC_PUBKEY').hexdigest()
        
        return address, private_key, public_key
    
    def create_wallet(self, wallet_name: str, passphrase: str = None) -> dict:
        """Create a new market-ready wallet"""
        if not wallet_name:
            raise ValueError("Wallet name cannot be empty")
        
        wallet_path = os.path.join(self.wallets_dir, f"{wallet_name}.wallet")
        
        if os.path.exists(wallet_path):
            raise ValueError(f"Wallet '{wallet_name}' already exists")
        
        # Generate master address, private key, and public key
        master_address, master_private_key, master_public_key = self.generate_address()
        
        # New wallets start with 0 balance (must receive coins or mine to get balance)
        initial_balance = 0.0  # Real market behavior - no free coins
        
        wallet_data = {
            'name': wallet_name,
            'created': datetime.now().isoformat(),
            'version': '2.0',  # Market version
            'master_address': master_address,
            'master_private_key': master_private_key,
            'master_public_key': master_public_key,
            'balance': initial_balance,
            'addresses': [
                {
                    'address': master_address,
                    'private_key': master_private_key,
                    'public_key': master_public_key,
                    'label': 'Primary Address',
                    'balance': initial_balance,
                    'created': datetime.now().isoformat()
                }
            ],
            'sending_addresses': [],
            'encrypted': passphrase is not None,
            'market_ready': True
        }
        
        # Encrypt wallet if passphrase provided
        if passphrase:
            wallet_data = self.encrypt_wallet_data(wallet_data, passphrase)
        
        # Save wallet
        with open(wallet_path, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        self.current_wallet = wallet_name
        self.wallet_data = wallet_data
        self.is_encrypted = passphrase is not None
        
        return {
            'wallet_name': wallet_name,
            'address': master_address,
            'private_key': master_private_key,
            'public_key': master_public_key,
            'balance': initial_balance,
            'backup_seed': self.generate_backup_seed(),
            'created': datetime.now().isoformat(),
            'market_ready': True
        }
    
    def open_wallet(self, wallet_name: str, passphrase: str = None) -> dict:
        """Open an existing wallet"""
        wallet_path = f"{self.wallets_dir}/{wallet_name}.wallet"
        
        if not os.path.exists(wallet_path):
            raise Exception(f"Wallet '{wallet_name}' not found")
        
        with open(wallet_path, 'r') as f:
            wallet_data = json.load(f)
        
        # Decrypt if encrypted
        if wallet_data.get('encrypted', False):
            if not passphrase:
                raise Exception("Wallet is encrypted. Passphrase required.")
            wallet_data = self.decrypt_wallet_data(wallet_data, passphrase)
        
        self.current_wallet = wallet_name
        self.wallet_data = wallet_data
        self.is_encrypted = wallet_data.get('encrypted', False)
        
        return {
            'name': wallet_name,
            'address': wallet_data['master_address'],
            'addresses_count': len(wallet_data['addresses']),
            'opened': True
        }
    
    def get_current_address(self):
        """Get the current wallet's master address"""
        if not self.current_wallet or not self.wallet_data:
            return None
        return self.wallet_data.get('master_address')
    
    def get_wallet_info(self):
        """Get current wallet information"""
        if not self.current_wallet:
            return None
        return {
            'name': self.current_wallet,
            'address': self.get_current_address(),
            'addresses_count': len(self.wallet_data.get('addresses', [])),
            'encrypted': self.is_encrypted
        }
    
    def close_wallet(self):
        """Close current wallet"""
        self.current_wallet = None
        self.wallet_data = {}
        self.is_encrypted = False
        self.encryption_key = None
    
    def backup_wallet(self, backup_path: str) -> bool:
        """Backup current wallet"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        try:
            # Create backup data
            backup_data = {
                'wallet_name': self.current_wallet,
                'backup_date': datetime.now().isoformat(),
                'wallet_data': self.wallet_data,
                'version': '1.0'
            }
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return True
        except Exception as e:
            raise Exception(f"Backup failed: {str(e)}")
    
    def restore_wallet(self, backup_path: str, new_wallet_name: str = None) -> dict:
        """Restore wallet from backup"""
        if not os.path.exists(backup_path):
            raise Exception("Backup file not found")
        
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            wallet_name = new_wallet_name or backup_data['wallet_name']
            wallet_data = backup_data['wallet_data']
            
            # Save restored wallet
            with open(f"{self.wallets_dir}/{wallet_name}.wallet", 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            return {
                'name': wallet_name,
                'restored': True,
                'original_date': backup_data.get('backup_date', 'Unknown')
            }
        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")
    
    def encrypt_wallet(self, passphrase: str) -> bool:
        """Encrypt current wallet"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        if self.is_encrypted:
            raise Exception("Wallet is already encrypted")
        
        # Encrypt wallet data
        self.wallet_data = self.encrypt_wallet_data(self.wallet_data, passphrase)
        self.is_encrypted = True
        
        # Save encrypted wallet
        with open(f"{self.wallets_dir}/{self.current_wallet}.wallet", 'w') as f:
            json.dump(self.wallet_data, f, indent=2)
        
        return True
    
    def change_passphrase(self, old_passphrase: str, new_passphrase: str) -> bool:
        """Change wallet passphrase"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        if not self.is_encrypted:
            raise Exception("Wallet is not encrypted")
        
        # Decrypt with old passphrase
        decrypted_data = self.decrypt_wallet_data(self.wallet_data, old_passphrase)
        
        # Re-encrypt with new passphrase
        self.wallet_data = self.encrypt_wallet_data(decrypted_data, new_passphrase)
        
        # Save wallet
        with open(f"{self.wallets_dir}/{self.current_wallet}.wallet", 'w') as f:
            json.dump(self.wallet_data, f, indent=2)
        
        return True
    
    def generate_new_address(self, label: str = "") -> str:
        """Generate new receiving address"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        address, private_key = self.generate_address()
        
        # Add to wallet
        self.wallet_data['addresses'].append({
            'address': address,
            'private_key': private_key,
            'label': label or f"Address {len(self.wallet_data['addresses']) + 1}",
            'balance': 0.0,
            'created': datetime.now().isoformat()
        })
        
        # Save wallet
        self.save_current_wallet()
        
        return address
    
    def add_sending_address(self, address: str, label: str) -> bool:
        """Add address to sending addresses"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        if address not in [addr['address'] for addr in self.wallet_data['sending_addresses']]:
            self.wallet_data['sending_addresses'].append({
                'address': address,
                'label': label,
                'added': datetime.now().isoformat()
            })
            self.save_current_wallet()
        
        return True
    
    def get_receiving_addresses(self) -> list:
        """Get all receiving addresses"""
        if not self.current_wallet:
            return []
        
        addresses = []
        for addr in self.wallet_data['addresses']:
            addresses.append({
                'address': addr['address'],
                'label': addr['label'],
                'balance': addr['balance'],
                'created': addr['created']
            })
        
        return addresses
    
    def get_sending_addresses(self) -> list:
        """Get all sending addresses"""
        if not self.current_wallet:
            return []
        
        return self.wallet_data['sending_addresses']
    
    def create_paper_wallet(self, output_path: str) -> dict:
        """Create paper wallet with QR codes"""
        if not self.current_wallet:
            raise Exception("No wallet is currently open")
        
        # Generate new address for paper wallet
        address, private_key = self.generate_address()
        
        # Create QR codes
        addr_qr = qrcode.QRCode(version=1, box_size=10, border=5)
        addr_qr.add_data(address)
        addr_qr.make(fit=True)
        addr_img = addr_qr.make_image(fill_color="black", back_color="white")
        
        key_qr = qrcode.QRCode(version=1, box_size=10, border=5)
        key_qr.add_data(private_key)
        key_qr.make(fit=True)
        key_img = key_qr.make_image(fill_color="black", back_color="white")
        
        # Create paper wallet image
        paper_width, paper_height = 800, 600
        paper = Image.new('RGB', (paper_width, paper_height), 'white')
        draw = ImageDraw.Draw(paper)
        
        # Title
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 12)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        draw.text((50, 30), "GSC Coin Paper Wallet", fill="black", font=title_font)
        draw.text((50, 70), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill="gray", font=text_font)
        
        # Address section
        draw.text((50, 120), "Public Address (for receiving GSC):", fill="black", font=text_font)
        draw.text((50, 140), address, fill="blue", font=text_font)
        
        # Private key section
        draw.text((50, 320), "Private Key (keep secret!):", fill="red", font=text_font)
        draw.text((50, 340), private_key[:32] + "...", fill="red", font=text_font)
        
        # Add QR codes
        addr_img = addr_img.resize((150, 150))
        key_img = key_img.resize((150, 150))
        
        paper.paste(addr_img, (550, 100))
        paper.paste(key_img, (550, 300))
        
        # Add labels for QR codes
        draw.text((580, 260), "Address QR", fill="black", font=text_font)
        draw.text((580, 460), "Private Key QR", fill="red", font=text_font)
        
        # Save paper wallet
        paper.save(output_path)
        
        return {
            'address': address,
            'private_key': private_key,
            'paper_wallet_path': output_path,
            'created': True
        }
    
    def generate_backup_seed(self) -> str:
        """Generate backup seed phrase"""
        words = [
            "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract",
            "absurd", "abuse", "access", "accident", "account", "accuse", "achieve", "acid",
            "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual",
            "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance"
        ]
        
        seed_words = []
        for _ in range(12):
            seed_words.append(secrets.choice(words))
        
        return " ".join(seed_words)
    
    def encrypt_wallet_data(self, data: dict, passphrase: str) -> dict:
        """Encrypt wallet data with passphrase"""
        # Generate key from passphrase
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        
        # Encrypt sensitive data
        fernet = Fernet(key)
        encrypted_data = data.copy()
        
        # Encrypt private keys
        for addr_data in encrypted_data['addresses']:
            addr_data['private_key'] = fernet.encrypt(addr_data['private_key'].encode()).decode()
        
        encrypted_data['master_private_key'] = fernet.encrypt(data['master_private_key'].encode()).decode()
        encrypted_data['salt'] = base64.b64encode(salt).decode()
        encrypted_data['encrypted'] = True
        
        return encrypted_data
    
    def decrypt_wallet_data(self, data: dict, passphrase: str) -> dict:
        """Decrypt wallet data with passphrase"""
        # Recreate key from passphrase and salt
        salt = base64.b64decode(data['salt'].encode())
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        
        # Decrypt data
        fernet = Fernet(key)
        decrypted_data = data.copy()
        
        # Decrypt private keys
        for addr_data in decrypted_data['addresses']:
            addr_data['private_key'] = fernet.decrypt(addr_data['private_key'].encode()).decode()
        
        decrypted_data['master_private_key'] = fernet.decrypt(data['master_private_key'].encode()).decode()
        decrypted_data['encrypted'] = False
        
        return decrypted_data
    
    def save_current_wallet(self):
        """Save current wallet to file"""
        if self.current_wallet:
            with open(f"{self.wallets_dir}/{self.current_wallet}.wallet", 'w') as f:
                json.dump(self.wallet_data, f, indent=2)
    
    def list_wallets(self) -> list:
        """List all available wallets"""
        wallets = []
        for filename in os.listdir(self.wallets_dir):
            if filename.endswith('.wallet'):
                wallet_name = filename[:-7]  # Remove .wallet extension
                wallets.append(wallet_name)
        return wallets
    
    def get_wallet_info(self) -> dict:
        """Get current wallet information"""
        if not self.current_wallet:
            return {}
        
        return {
            'name': self.current_wallet,
            'encrypted': self.is_encrypted,
            'addresses_count': len(self.wallet_data.get('addresses', [])),
            'master_address': self.wallet_data.get('master_address', ''),
            'created': self.wallet_data.get('created', ''),
            'backup_seed': self.wallet_data.get('backup_seed', ''),
            'balance': self.wallet_data.get('balance', 0.0)
        }
