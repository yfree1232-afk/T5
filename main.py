#!/usr/bin/env python3
"""
🌸 Shizuka Bot - Advanced Telegram Economy Bot 🌸
Entry point with retry logic and graceful error handling
"""
import sys
import logging
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from shizuka_bot.app import main

# Configure basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    print("\n" + "🌸"*20)
    print("SHIZUKA BOT - LAUNCHER")
    print("🌸"*20 + "\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Bot stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
