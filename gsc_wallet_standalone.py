#!/usr/bin/env python3
"""
GSC Coin Wallet - Standalone Executable Version
Optimized for easy deployment and node connectivity
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_and_install_dependencies():
    """Check and install required dependencies silently"""
    required_packages = {
        'cryptography': 'cryptography>=3.4.8',
        'PIL': 'Pillow>=8.3.2',
        'qrcode': 'qrcode>=7.3.1',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package_name, pip_name in required_packages.items():
        try:
            if package_name == 'cryptography':
                import cryptography
            elif package_name == 'PIL':
                from PIL import Image
            elif package_name == 'qrcode':
                import qrcode
            elif package_name == 'matplotlib':
                import matplotlib
            elif package_name == 'numpy':
                import numpy
        except ImportError:
            missing_packages.append(pip_name.split('>=')[0])
    
    if missing_packages:
        print("Installing required packages...")
        import subprocess
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"Warning: Could not install {package}")
    
    return True

def setup_data_directory():
    """Setup data directory for blockchain storage"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = current_dir
    
    data_dir = os.path.join(app_dir, 'gsc_data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Set blockchain data file path
    blockchain_file = os.path.join(data_dir, 'gsc_blockchain.json')
    return data_dir, blockchain_file

def connect_to_known_nodes(network_node):
    """Connect to known GSC nodes for synchronization"""
    known_nodes = [
        ('127.0.0.1', 8333),
        ('localhost', 8333),
        ('127.0.0.1', 8334),
        ('127.0.0.1', 8335)
    ]
    
    def try_connect():
        time.sleep(2)  # Wait for our server to start
        for host, port in known_nodes:
            try:
                network_node.connect_to_peer(host, port)
                time.sleep(1)
            except:
                continue
    
    # Start connection attempts in background
    connect_thread = threading.Thread(target=try_connect)
    connect_thread.daemon = True
    connect_thread.start()

def main():
    """Main application entry point"""
    print("=" * 60)
    print("🪙 GSC COIN WALLET - STANDALONE VERSION 🪙")
    print("=" * 60)
    print("✅ Easy deployment - no installation required")
    print("✅ Automatic node discovery and synchronization")
    print("✅ Complete blockchain wallet functionality")
    print("✅ Mining and transaction capabilities")
    print()
    
    try:
        # Check dependencies
        check_and_install_dependencies()
        
        # Setup data directory
        data_dir, blockchain_file = setup_data_directory()
        print(f"Data directory: {data_dir}")
        
        # Import modules after dependency check
        from blockchain import GSCBlockchain
        from network import GSCNetworkNode
        from gsc_wallet_gui import GSCWalletGUI
        
        # Initialize blockchain with custom data path
        blockchain = GSCBlockchain()
        blockchain.data_file = blockchain_file
        
        # Try to load existing blockchain
        if os.path.exists(blockchain_file):
            try:
                blockchain.load_from_file(blockchain_file)
                print("✅ Existing blockchain loaded")
            except:
                print("⚠ Creating new blockchain")
        
        # Initialize network with fallback ports
        network_node = None
        for port in [8333, 8334, 8335, 8336]:
            try:
                network_node = GSCNetworkNode(blockchain, port=port)
                if network_node.start_server():
                    print(f"✅ P2P node started on port {port}")
                    break
            except:
                continue
        
        if not network_node:
            print("⚠ Running in offline mode")
            network_node = GSCNetworkNode(blockchain, port=8333)
        
        # Connect blockchain and network
        blockchain.set_network_node(network_node)
        
        # Attempt to connect to existing nodes
        if network_node:
            connect_to_known_nodes(network_node)
        
        # Launch GUI wallet
        print("🚀 Launching GSC Coin Wallet...")
        wallet = GSCWalletGUI(blockchain, network_node)
        
        # Set data directory for wallet
        wallet.data_dir = data_dir
        
        # Start wallet
        wallet.run()
        
    except ImportError as e:
        print(f"❌ Missing required modules: {e}")
        print("Please ensure all GSC Coin files are in the same directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Error starting GSC Coin: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
