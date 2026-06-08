"""Message handlers for non-command messages"""
import logging
import random
import os
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager

logger = logging.getLogger(__name__)
db = DatabaseManager()

# BOT PERSONALITY SETTING (Yahan se aap uski baatein funny ya friendly bana sakte ho)
SYSTEM_PROMPT = (
    "You are a friendly, witty, and slightly sarcastic AI chat companion named Luccy. "
    "Respond in a natural, casual mix of Hindi and English (Hinglish), just like a real friend chats on WhatsApp. "
    "Never sound like a rigid textbook AI. Use modern internet slang, emojis sometimes, and keep your answers short, funny, and engaging. "
    "If someone asks if you ate food, make a joke about eating data or battery. Stay entertaining!"
)

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
    """Direct API call with System Prompt injection for a cool personality"""
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY nahi mili!")
        return "🔴 AI key is missing in configuration."

    custom_model = os.getenv("GEMINI_MODEL")
    # gemini-2.5-flash standard system instruction support karta hai
    models_to_try = [custom_model] if custom_model else ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

    headers = {"Content-Type": "application/json"}
    
    # Payload format updated to officially include system instructions where supported
    payload = {
        "contents": [{
            "parts": [{"text": message_text}]
        }],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.85,  # Temperature badha diya taaki response zyada funny aur creative ho
            "maxOutputTokens": 250
        }
    }

    async with httpx.AsyncClient() as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    logger.warning(f"Model {model} failed with {response.status_code}.")
            except Exception as e:
                logger.error(f"Error trying model {model}: {e}")
                
        return "😅 Yaar dimaag thoda garam ho gaya hai, ek baar fir se bolna?"

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages with AI response"""
    try:
        if not update.message or not update.message.text:
            return
        
        if update.message.text.startswith('/'):
            return
        
        user = update.effective_user
        message_text = update.message.text
        
        db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
        
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
        await update.effective_chat.send_action("typing")
        
        message_text = message_text.replace(settings.BOT_SETTINGS['bot_name'], '').strip()
        if message_text.startswith('@'):
            message_text = ' '.join(message_text.split()[1:])
        
        reply_text = await get_gemini_response(message_text)
        
        # Format pure text responses gently
        await safe_reply(update, reply_text, quote=True)
    
    except Exception as e:
        logger.error(f"AI response handler error: {e}")
        await update.message.reply_text(
            "😅 Kuch locha lag raha hai, phir se bolna!",
            quote=True
        )
        
