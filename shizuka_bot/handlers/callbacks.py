"""Callback query handlers"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries from inline buttons"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("confirm_"):
            action = data.replace("confirm_", "")
            await query.edit_message_text(f"✅ Action confirmed: {action}")
        
        elif data.startswith("cancel_"):
            await query.edit_message_text("❌ Action cancelled")
        
        else:
            await query.answer("🔔 Button action not recognized", show_alert=True)
    
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        try:
            await update.callback_query.answer("❌ An error occurred", show_alert=True)
        except:
            pass
