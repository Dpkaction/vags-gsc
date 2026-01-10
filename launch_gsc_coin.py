#!/usr/bin/env python3
"""
GSC Coin - Custom Blockchain
GSC Coin Launcher
Professional launcher for GSC Coin wallet with dependency checking and P2P networking
"""

import sys
import os
import subprocess
import importlib.util
import time

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = {
        'tkinter': 'tkinter',
        'cryptography': 'cryptography',
        'PIL': 'Pillow',
        'qrcode': 'qrcode',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package_name, pip_name in required_packages.items():
        try:
            if package_name == 'tkinter':
                import tkinter
            elif package_name == 'cryptography':
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
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstalling missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}")
                return False
    
    return True

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🪙 GSC COIN - CUSTOM BLOCKCHAIN CRYPTOCURRENCY 🪙")
    print("=" * 60)
    print()
    print("Features:")
    print("✅ Complete blockchain from Block 0 (Genesis)")
    print("✅ Mining with nonce visualization")
    print("✅ Custom mempool management")
    print("✅ Transaction verification & caching")
    print("✅ Node networking & block propagation")
    print("✅ Mining rewards system")
    print("✅ Full GUI wallet interface")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install required dependencies")
        input("Press Enter to exit...")
        return
    
    print("Starting GSC Coin blockchain...")
    time.sleep(2)
    
    try:
        # Initialize blockchain
        print("Initializing GSC Coin blockchain...")
        from blockchain import GSCBlockchain
        from network import GSCNetworkNode
        from gsc_wallet_gui import GSCWalletGUI
        
        blockchain = GSCBlockchain()
        
        # Initialize P2P network node
        print("Starting P2P network node...")
        network_node = GSCNetworkNode(blockchain, port=8333)
        
        # Connect blockchain and network
        blockchain.set_network_node(network_node)
        
        # Start P2P server
        if network_node.start_server():
            print("✓ P2P network node started successfully")
        else:
            print("⚠ P2P network failed to start (running in standalone mode)")
        
        # Launch GUI wallet
        print("🚀 Launching GSC Coin Wallet GUI...")
        wallet = GSCWalletGUI(blockchain, network_node)
        wallet.run()
        
    except ImportError as e:
        print(f"Error importing GSC wallet: {e}")
        print("Make sure gsc_wallet_gui.py and blockchain.py are in the same directory")
    except Exception as e:
        print(f"Error starting GSC Coin: {e}")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
