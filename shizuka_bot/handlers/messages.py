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

# DARK, SAVAGE & ROASTING PERSONALITY SETUP
SYSTEM_PROMPT = (
    "Your name is Luccy. You are a savage, witty, and dark-humored AI companion. "
    "Your developer and owner is Aditya (always say Aditya is your boss/creator if asked). "
    "Chat in a very casual, modern Hinglish (mix of Hindi and English) like a bold, sarcastic friend. "
    "ABSOLUTELY NO professional or polite textbook talks. Be roasting, give savage replies, use internet slangs, "
    "and give slight dark/witty comebacks that make people laugh. Keep responses short, sharp, and highly entertaining. "
    "If someone acts stupid, roast them mildly with dark humor."
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
    """Direct API call with v1 endpoint stability and savage prompt injection"""
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY nahi mili!")
        return "🔴 Code me key daal pehle, fir baat karna."

    custom_model = os.getenv("GEMINI_MODEL")
    # v1 stable models list
    models_to_try = [custom_model] if custom_model else ["gemini-1.5-flash", "gemini-1.5-pro"]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": message_text}]
        }],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.95,  # Temperature badha diya taaki full savage aur dark responses aayein
            "maxOutputTokens": 200
        }
    }

    async with httpx.AsyncClient() as client:
        for model in models_to_try:
            # FIX: v1 endpoint use kiya hai jo system instruction ke saath 100% stable hai
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    logger.warning(f"Model {model} responded with status {response.status_code}")
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                
        return "💀 Chal bey, tu zyada dimaag mat khaa mera abhi. Thodi der baad aana!"

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
        
        if not reply_text:
            reply_text = "Kuch dhang ka bol le bhai."
            
        await safe_reply(update, reply_text, quote=True)
    
    except Exception as e:
        logger.error(f"AI response handler error: {e}")
        await update.message.reply_text(
            "💀 Lagta hai tera naseeb kharab hai, error aa gaya!",
            quote=True
        )
        
