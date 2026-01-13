"""Advanced configuration management with validation and environment support"""
import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """Advanced configuration with validation and fallback"""
    
    # ===== TOKEN & AUTHENTICATION =====
    TOKEN: str = os.getenv('BOT_TOKEN', '8438940989:AAFP6dkFWGzYZ6v8pJeFByX8yxJ7KgOzRf0')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', 'AIzaSyAHJASpFanIZ1FHD7D-zzpUrIzcbEv5qr8')
    BOT_OWNER_ID: int = int(os.getenv('BOT_OWNER_ID', '5536920122'))
    ADMIN_IDS: List[int] = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    
    # ===== DATABASE =====
    DATABASE_FILE: str = os.getenv('DATABASE_FILE', 'shizuka_world.db')
    DB_CHECK_SAME_THREAD: bool = False
    DB_TIMEOUT: int = 30
    DB_MAX_CONNECTIONS: int = 20
    
    # ===== PERFORMANCE & LOAD HANDLING =====
    WORKER_THREADS: int = int(os.getenv('WORKER_THREADS', '8'))
    CONNECTION_POOL_SIZE: int = int(os.getenv('CONN_POOL_SIZE', '10'))
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '30'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds
    
    # ===== LOGGING =====
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'shizuka_bot/logs/bot.log')
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    
    # ===== BOT SETTINGS (Can be modified by owner) =====
    BOT_SETTINGS: Dict[str, Any] = {
        "show_protection_time": True,
        "kill_success_rate": 50,
        "rob_success_rate": 40,
        "kill_fail_cooldown": 30,
        "kill_cost": 500,
        "revive_cost": 1000,
        "rob_cooldown": 60,
        "protection_prices": {1: 200, 2: 400, 3: 600},
        "daily_bonus_base": 100,
        "work_min": 100,
        "work_max": 500,
        "tax_rate": 10,
        "default_currency": "$",
        "bot_name": "@ImShizukaBot",
        "wordgame_min_players": 2,
        "wordgame_max_players": 10,
        "bombgame_min_players": 2,
        "bombgame_max_players": 10,
        "leave_penalty": 10,
        "max_items_per_page": 10,
        "min_deposit": 10,
        "min_withdraw": 10,
        "bank_interest": 0.1,
        "lottery_ticket_price": 100,
        "lottery_prize_base": 1000,
        "max_bank_percentage": 70,
        "max_games_per_group": 12,
        "game_wait_time": 180,
        "bank_deposit_fee": 1,
        "bank_withdraw_fee": 2,
        "couple_show_duration": 24,
        "pin_duration": 24,
        "reaction_good": "❤️",
        "reaction_bad": "👎",
        "reaction_chance": 30,
        "max_players_custom": 20
    }
    
    # ===== DEFAULT SHOP ITEMS =====
    DEFAULT_ITEMS: List[Dict[str, Any]] = [
        {"name": "Chocolate 🍫", "price": 1000, "emoji": "🍫", "description": "Sweet chocolate for your loved one"},
        {"name": "Rose 🌹", "price": 500, "emoji": "🌹", "description": "Beautiful red rose"},
        {"name": "Diamond 💎", "price": 10000, "emoji": "💎", "description": "Precious diamond"},
        {"name": "Cake 🎂", "price": 2000, "emoji": "🎂", "description": "Delicious birthday cake"},
        {"name": "Teddy Bear 🧸", "price": 1500, "emoji": "🧸", "description": "Cuddly teddy bear"},
        {"name": "Love Letter 💌", "price": 300, "emoji": "💌", "description": "Romantic love letter"},
        {"name": "Ring 💍", "price": 5000, "emoji": "💍", "description": "Promise ring"},
        {"name": "Bouquet 💐", "price": 1200, "emoji": "💐", "description": "Beautiful flower bouquet"},
        {"name": "Golden Crown 👑", "price": 50000, "emoji": "👑", "description": "Royal golden crown"},
        {"name": "Mystery Box 🎁", "price": 3000, "emoji": "🎁", "description": "Mystery gift box"}
    ]
    
    @classmethod
    def validate_token(cls) -> bool:
        """Validate token format"""
        if not cls.TOKEN:
            raise ValueError("❌ BOT_TOKEN is empty")
        if ':' not in cls.TOKEN:
            raise ValueError("❌ BOT_TOKEN format invalid - must contain ':'")
        if len(cls.TOKEN.split(':')) != 2:
            raise ValueError("❌ BOT_TOKEN format invalid - must be 'ID:KEY'")
        return True
    
    @classmethod
    def validate_config(cls) -> bool:
        """Full configuration validation"""
        try:
            # Validate token
            cls.validate_token()
            
            # Validate IDs
            if not isinstance(cls.BOT_OWNER_ID, int):
                raise ValueError("❌ BOT_OWNER_ID must be integer")
            
            # Validate database file path
            if not cls.DATABASE_FILE:
                raise ValueError("❌ DATABASE_FILE is empty")
            
            # Validate performance settings
            if cls.WORKER_THREADS < 1:
                raise ValueError("❌ WORKER_THREADS must be >= 1")
            
            # Validate rate limiting
            if cls.RATE_LIMIT_REQUESTS < 1 or cls.RATE_LIMIT_WINDOW < 1:
                raise ValueError("❌ Rate limit settings invalid")
            
            logger.info("✅ Configuration validated successfully")
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

# Global settings instance
settings = Config()
