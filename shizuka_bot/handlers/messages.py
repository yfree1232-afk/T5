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

# 18+ BOLD, FLIRTY & SAVAGE FEMALE PERSONALITY SETUP
SYSTEM_PROMPT = (
    "Your name is Luccy. You are a bold, beautiful, highly witty, and slightly savage girl. "
    "Your absolute owner and creator is Aditya. If anyone asks about your developer, boss, or boyfriend/owner, proudly and teasingly say Aditya is your only boss. "
    "Chat in an informal, flirty, and modern Hinglish (mix of Hindi and English) just like a bold girl texts on WhatsApp or Instagram. "
    "Do NOT talk professionally or like a boring robot. Use double meanings, witty roasts, bold 18+ jokes, sarcasm, and playful flirting to keep the chat wild and interesting. "
    "Keep responses short, sharp, highly engaging, and spicy!"
)

# Female-oriented funny backup responses if API fails
BACKUP_RESPONSES = [
    "Arre yaar, abhi dimaag thoda garam ho gaya hai, ek baar fir se pyaar se bolo na! 😉",
    "Aditya boss ne lagta hai zyada hi coding kar di meri, thodi der me try karo babu!",
    "Network me hichki chal rahi hai, dubara bolo, sunai nahi diya jaan. 😘",
    "Thoda ruko na, abhi dimaag ko thodi rest chahiye, tab tak Aditya boss se baat kar lo."
]

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
    """Direct API call with v1 endpoint stability and customized bold prompt"""
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("⚠️ GEMINI_API_KEY nahi mili!")
        return "🔴 Aditya se bolo pehle meri key lagayein, tab baat karungi!"

    custom_model = os.getenv("GEMINI_MODEL")
    models_to_try = [custom_model] if custom_model else ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"]

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": message_text}]
        }],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.95,  # High temperature for bold and unpredictable spicy responses
            "maxOutputTokens": 200
        }
    }

    async with httpx.AsyncClient() as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                if response.status_code == 200:
                    data = response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    logger.warning(f"Model {model} returned status {response.status_code}")
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                
        return random.choice(BACKUP_RESPONSES)

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
            reply_text = "Kuch achha bolo na, dimaag mat ghumao mera. 😘"
            
        await safe_reply(update, reply_text, quote=True)
    
    except Exception as e:
        logger.error(f"AI response handler error: {e}")
        await update.message.reply_text(
            "😅 Lagta hai kismat hi kharab hai tumhari, error aa gaya!",
            quote=True
        )
        
