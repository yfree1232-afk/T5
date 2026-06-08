"""Message handlers for non-command messages"""
import logging
import random
import os
import httpx  # <-- Direct API request bhejne ke liye
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

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

async def get_gemini_response(message_text: str) -> str:
    """Direct API call to bypass outdated python library issues"""
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY nahi mili!")
        return "🔴 AI key is missing in configuration."

    chosen_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": message_text}]
        }],
        "generationConfig": {
            "maxOutputTokens": 200,
            "temperature": 0.7
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                # Parse the response text safely
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.error(f"Gemini API Http Error {response.status_code}: {response.text}")
                return "😅 I'm having trouble connecting to my brain right now."
        except Exception as e:
            logger.error(f"Error during direct Gemini API hit: {e}")
            return "😅 Something went wrong while thinking."

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
            await handle_ai_message(update, message_text)
        elif "@" in message_text and settings.BOT_SETTINGS['bot_name'] in message_text:
            await handle_ai_message(update, message_text)
        elif update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
            await handle_ai_message(update, message_text)
    
    except Exception as e:
        logger.error(f"Message handler error: {e}", exc_info=True)

async def handle_ai_message(update: Update, message_text: str):
    """Handle message with AI response"""
    try:
        # Show typing indicator
        await update.effective_chat.send_action("typing")
        
        # Clean message from bot mentions
        message_text = message_text.replace(settings.BOT_SETTINGS['bot_name'], '').strip()
        if message_text.startswith('@'):
            message_text = ' '.join(message_text.split()[1:])
        
        # Direct HTTP bypass request call
        reply_text = await get_gemini_response(message_text)
        
        if reply_text:
            reply_text = reply_text[:500]
        else:
            reply_text = "I couldn't generate a response."
        
        await safe_reply(update, f"🤖 {reply_text}", parse_mode=ParseMode.HTML, quote=True)
    
    except Exception as e:
        logger.error(f"AI response handler error: {e}")
        await update.message.reply_text(
            "😅 I had trouble understanding that. Try rephrasing!",
            quote=True
        )
        
