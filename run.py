#!/usr/bin/env python3
"""
GSC Coin - Quick Run Script
Simple launcher for GSC Coin wallet
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from launch_gsc_coin import main
    main()
except ImportError as e:
    print("Error importing GSC Coin modules: {}".format(e))
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print("============================================================")
    print("=== GSC COIN - CUSTOM BLOCKCHAIN CRYPTOCURRENCY ===")
    print("============================================================")
    print()
    print("Features:")
    print("[+] Complete blockchain from Block 0 (Genesis)")
    print("[+] Mining with nonce visualization")
    print("[+] Custom mempool management")
    print("[+] Transaction verification & caching")
    print("[+] Node networking & block propagation")
    print("[+] Mining rewards system")
    print("[+] Full GUI wallet interface")
    print("[+] Bitcoin-style sync pipeline")
    print("[+] Mandatory mining address enforcement")
    print("[+] Mempool import/export functionality")
    print("[+] Blockchain import/export functionality")
    print("Error launching GSC Coin: {}".format(e))
    sys.exit(1)
