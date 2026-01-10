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
    print(f"Error importing GSC Coin modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error launching GSC Coin: {e}")
    sys.exit(1)
