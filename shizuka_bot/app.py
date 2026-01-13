"""Main bot application"""
import logging
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import InvalidToken

from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager
from shizuka_bot.utils import setup_logging, error_handler
from shizuka_bot.handlers import (
    start_command, help_command, profile_command, balance_command,
    daily_command, work_command, top_command, kill_command, rob_command,
    protect_command, revive_command, give_command, items_command,
    buy_command, sell_command, price_command, setprice_command,
    deposit_command, withdraw_command, couples_command, kick_command,
    ban_command, unban_command, mute_command, unmute_command,
    warn_command, look_command, brain_command, book_command,
    bomb_command, wordgame_command, spin_command,
    callback_handler, message_handler
)

# Setup logging
logger = setup_logging()

class ShizukaBot:
    """Main bot application with advanced features"""
    
    def __init__(self):
        self.config = settings
        self.db = DatabaseManager()
        self.application = None
        self.logger = logger
    
    def validate_configuration(self) -> bool:
        """Validate all configuration"""
        try:
            self.logger.info("Validating configuration...")
            
            # Validate token
            self.config.validate_token()
            self.logger.info("✅ Token format valid")
            
            # Validate full config
            self.config.validate_config()
            self.logger.info("✅ Full configuration validated")
            
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            print(f"❌ Configuration Error: {e}")
            return False
    
    def register_handlers(self) -> None:
        """Register all command and message handlers"""
        try:
            # Basic commands
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))
            
            # Economy commands
            self.application.add_handler(CommandHandler("profile", profile_command))
            self.application.add_handler(CommandHandler("balance", balance_command))
            self.application.add_handler(CommandHandler("daily", daily_command))
            self.application.add_handler(CommandHandler("work", work_command))
            self.application.add_handler(CommandHandler("top", top_command))
            self.application.add_handler(CommandHandler("deposit", deposit_command))
            self.application.add_handler(CommandHandler("withdraw", withdraw_command))
            self.application.add_handler(CommandHandler("give", give_command))
            
            # PVP commands
            self.application.add_handler(CommandHandler("kill", kill_command))
            self.application.add_handler(CommandHandler("rob", rob_command))
            self.application.add_handler(CommandHandler("protect", protect_command))
            self.application.add_handler(CommandHandler("revive", revive_command))
            
            # Shop commands
            self.application.add_handler(CommandHandler("items", items_command))
            self.application.add_handler(CommandHandler("buy", buy_command))
            self.application.add_handler(CommandHandler("sell", sell_command))
            self.application.add_handler(CommandHandler("price", price_command))
            self.application.add_handler(CommandHandler("setprice", setprice_command))
            
            # Relationship commands
            self.application.add_handler(CommandHandler("couples", couples_command))
            
            # Moderation commands
            self.application.add_handler(CommandHandler("warn", warn_command))
            self.application.add_handler(CommandHandler("kick", kick_command))
            self.application.add_handler(CommandHandler("ban", ban_command))
            self.application.add_handler(CommandHandler("unban", unban_command))
            self.application.add_handler(CommandHandler("mute", mute_command))
            self.application.add_handler(CommandHandler("unmute", unmute_command))
            
            # Fun commands
            self.application.add_handler(CommandHandler("look", look_command))
            self.application.add_handler(CommandHandler("brain", brain_command))
            self.application.add_handler(CommandHandler("book", book_command))
            
            # Game commands
            self.application.add_handler(CommandHandler("bomb", bomb_command))
            self.application.add_handler(CommandHandler("wordgame", wordgame_command))
            self.application.add_handler(CommandHandler("spin", spin_command))
            
            # Callback and message handlers
            self.application.add_handler(CallbackQueryHandler(callback_handler))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
            
            # Error handler (must be last)
            self.application.add_error_handler(error_handler)
            
            self.logger.info(f"✅ Registered {len(self.application.handlers)} handler groups")
        except Exception as e:
            self.logger.error(f"Handler registration error: {e}")
            raise
    
    def start(self) -> None:
        """Start the bot"""
        try:
            # Validate configuration
            if not self.validate_configuration():
                sys.exit(1)
            
            self.logger.info("Creating bot application...")
            
            # Create application
            self.application = Application.builder()\
                .token(self.config.TOKEN.strip())\
                .concurrent_updates(True)\
                .post_init(self._post_init)\
                .build()
            
            # Register handlers
            self.register_handlers()
            
            # Print startup info
            print("\n" + "="*60)
            print(f"🌸 {self.config.BOT_SETTINGS['bot_name']} - STARTING UP...")
            print("="*60)
            print("✨ FEATURES:")
            print("   💰 Complete Economy System")
            print("   🎮 Game Management")
            print("   ⚔️ PVP System (Kill, Rob, Protect)")
            print("   🛍️ Shop & Items System")
            print("   👥 Relationship System")
            print("   🛡️ Moderation Tools")
            print("   🤖 AI Chat with Gemini")
            print("="*60)
            print("✅ Database: Initialized with Foreign Key constraints")
            print("✅ Config: Validated successfully")
            print("✅ Handlers: All registered and ready")
            print("="*60)
            print()
            
            self.logger.info("🚀 Starting polling...")
            
            # Start polling (synchronous method that runs the event loop internally)
            self.application.run_polling(allowed_updates=["message", "callback_query"])
        
        except InvalidToken as e:
            self.logger.critical(f"❌ INVALID TOKEN: {e}")
            print(f"❌ Invalid Telegram token - cannot connect to API")
            sys.exit(1)
        except Exception as e:
            self.logger.critical(f"❌ FATAL ERROR: {e}", exc_info=True)
            print(f"❌ Fatal error: {e}")
            sys.exit(1)
    
    async def _post_init(self, application: Application) -> None:
        """Post-initialization tasks"""
        self.logger.info("Post-init: Bot connection established")

def main():
    """Main entry point"""
    import asyncio
    bot = ShizukaBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
        sys.exit(0)
