"""Message handlers for non-command messages"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import google.generativeai as genai

from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def safe_reply(update, text, parse_mode=None, **kwargs):
    """Send reply safely; fallback to plain text on parse errors"""
    try:
        if update and getattr(update, "message", None):
            await update.message.reply_text(text, parse_mode=parse_mode, **kwargs)
        else:
            await update.effective_message.reply_text(text, parse_mode=parse_mode, **kwargs)
    except Exception as e:
        logger.warning(f"AI reply failed with {e}; sending plain text")
        if update and getattr(update, "message", None):
            await update.message.reply_text(text, **kwargs)
        else:
            await update.effective_message.reply_text(text, **kwargs)

# Initialize Gemini if API key available
gemini_model = None
try:
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-pro')
        logger.info("✅ Gemini AI initialized")
except Exception as e:
    logger.warning(f"⚠️ Gemini initialization failed: {e}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages with AI response"""
    try:
        if not update.message or not update.message.text:
            return
        
        # Skip commands
        if update.message.text.startswith('/'):
            return
        
        user = update.effective_user
        message_text = update.message.text
        
        # Ensure user exists in database
        db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
        
        # Check if message mentions bot or is a reply to bot
        if update.effective_chat.type == "private":
            # Private chat - always respond
            await handle_ai_message(update, message_text)
        elif "@" in message_text and settings.BOT_SETTINGS['bot_name'] in message_text:
            # Mentioned in group
            await handle_ai_message(update, message_text)
        elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
            # Reply to bot message
            await handle_ai_message(update, message_text)
    
    except Exception as e:
        logger.error(f"Message handler error: {e}", exc_info=True)

async def handle_ai_message(update: Update, message_text: str):
    """Handle message with AI response"""
    try:
        # Show typing indicator
        await update.effective_chat.send_action("typing")
        
        if not gemini_model:
            await update.message.reply_text(
                "🔴 AI service temporarily unavailable. Try again later!",
                quote=True
            )
            return
        
        # Clean message
        message_text = message_text.replace(settings.BOT_SETTINGS['bot_name'], '').strip()
        if message_text.startswith('@'):
            message_text = ' '.join(message_text.split()[1:])
        
        # Get AI response
        response = gemini_model.generate_content(
            message_text,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.7,
            )
        )
        
        reply_text = response.text[:500] if response.text else "I couldn't generate a response."
        
        await safe_reply(update, f"🤖 {reply_text}", parse_mode=ParseMode.HTML, quote=True)
    
    except Exception as e:
        logger.error(f"AI response error: {e}")
        await update.message.reply_text(
            "😅 I had trouble understanding that. Try rephrasing!",
            quote=True
        )
