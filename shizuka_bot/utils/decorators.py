"""Advanced decorators for performance and reliability"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Dict
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Rate limiting store
_rate_limit_store: Dict[int, list] = defaultdict(list)

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"❌ All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def rate_limit(requests: int = 30, window: int = 60):
    """Decorator for rate limiting per user"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            current_time = time.time()
            
            # Clean old requests
            _rate_limit_store[user_id] = [
                req_time for req_time in _rate_limit_store[user_id]
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(_rate_limit_store[user_id]) >= requests:
                logger.warning(f"⚠️ Rate limit exceeded for user {user_id}")
                await update.effective_message.reply_text(
                    "⏱️ You're using commands too fast. Please wait a moment."
                )
                return
            
            # Record request
            _rate_limit_store[user_id].append(current_time)
            
            # Execute function
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def async_task():
    """Decorator for running task in background without blocking"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create task and let it run in background
            asyncio.create_task(func(*args, **kwargs))
        return wrapper
    return decorator

def validate_owner(func: Callable) -> Callable:
    """Decorator to ensure only bot owner can execute command"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from shizuka_bot.config import settings
        
        user_id = update.effective_user.id
        if user_id != settings.BOT_OWNER_ID and user_id not in settings.ADMIN_IDS:
            await update.effective_message.reply_text("❌ You don't have permission to use this command.")
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper

def validate_admin(func: Callable) -> Callable:
    """Decorator to ensure user is admin"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type == "private":
            return await func(update, context, *args, **kwargs)
        
        user = await update.effective_chat.get_member(update.effective_user.id)
        if user.status not in ["administrator", "creator"]:
            await update.effective_message.reply_text("❌ You must be a group administrator to use this command.")
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
