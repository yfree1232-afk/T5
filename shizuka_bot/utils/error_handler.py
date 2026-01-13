"""Advanced error handling"""
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest, NetworkError, TimedOut, InvalidToken

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Central error handler for all bot errors"""
    
    @staticmethod
    async def handle_telegram_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Telegram API errors"""
        error = context.error
        
        if isinstance(error, InvalidToken):
            logger.critical("❌ INVALID BOT TOKEN - Cannot connect to Telegram API")
            return
        
        if isinstance(error, NetworkError):
            logger.warning(f"⚠️ Network error: {error}")
            return
        
        if isinstance(error, TimedOut):
            logger.warning("⚠️ Request timeout - retrying...")
            return
        
        if isinstance(error, Forbidden):
            logger.error(f"❌ Forbidden - Bot was kicked from group or user blocked: {error}")
            return
        
        if isinstance(error, BadRequest):
            logger.error(f"❌ Bad request: {error}")
            return
        
        if isinstance(error, TelegramError):
            logger.error(f"❌ Telegram error: {error}")
            return
        
        # Generic error
        logger.error(f"❌ Unhandled error: {type(error).__name__}: {error}", exc_info=True)
    
    @staticmethod
    async def handle_command_error(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   command: str, error: Exception):
        """Handle command execution errors"""
        logger.error(f"❌ Error in {command}: {error}", exc_info=True)
        
        try:
            if update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred while processing your request. Please try again."
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    @staticmethod
    async def handle_callback_error(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   error: Exception):
        """Handle callback query errors"""
        logger.error(f"❌ Callback error: {error}", exc_info=True)
        
        try:
            if update.callback_query:
                await update.callback_query.answer(
                    "❌ An error occurred. Please try again.",
                    show_alert=True
                )
        except Exception as e:
            logger.error(f"Failed to send callback error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main error handler for application"""
    try:
        await ErrorHandler.handle_telegram_error(update, context)
    except Exception as e:
        logger.critical(f"❌ CRITICAL ERROR in error handler: {e}", exc_info=True)
