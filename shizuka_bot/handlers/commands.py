"""Command handlers - All user-facing commands"""
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager
from shizuka_bot.utils.decorators import rate_limit, retry_on_error, validate_owner, validate_admin
from shizuka_bot.managers import GameManager, EconomyManager, ModeratorManager

logger = logging.getLogger(__name__)
db = DatabaseManager()
game_mgr = GameManager()
economy_mgr = EconomyManager()
mod_mgr = ModeratorManager()

async def safe_reply(update, text, parse_mode=None, **kwargs):
    """Send a reply safely; fallback to plain text on parse/Telegram errors"""
    try:
        if update and getattr(update, "message", None):
            await update.message.reply_text(text, parse_mode=parse_mode, **kwargs)
        else:
            await update.effective_message.reply_text(text, parse_mode=parse_mode, **kwargs)
    except Exception as e:
        logger.warning(f"Reply failed with {e}; sending plain text")
        if update and getattr(update, "message", None):
            await update.message.reply_text(text, **kwargs)
        else:
            await update.effective_message.reply_text(text, **kwargs)

def format_money(amount: int) -> str:
    """Format money with currency symbol"""
    return f"💵 {amount:,} {settings.BOT_SETTINGS['default_currency']}"

# ===== BASIC COMMANDS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    try:
        user = update.effective_user
        db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
        
        await update.message.reply_text(
            f"""🌸 *Welcome to {settings.BOT_SETTINGS['bot_name']}!* 🌸

👋 *Hello {user.first_name}!*

This is a comprehensive economy bot with:
💰 *Economy System* - Balance, bank, work, daily rewards
🎮 *Games* - Bomb, wordgame, spin, and more
⚔️ *PVP System* - Kill, rob, protect with rewards
🛍️ *Shop* - Buy and sell items
👥 *Relationships* - Get married, build couples
🛡️ *Moderation* - Admin tools for groups

Use /help to see all commands!
            """,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text("❌ An error occurred")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with all commands"""
    help_text = """🌸 *SHIZUKA BOT - COMPLETE COMMAND LIST* 🌸

*💰 ECONOMY COMMANDS:*
/profile - View your profile
/balance - Check balance
/daily - Daily reward (24h cooldown)
/work - Work for money
/top [field] - Top users leaderboard
/deposit amount - Deposit to bank
/withdraw amount - Withdraw from bank

*⚔️ PVP COMMANDS:*
/kill @user - Try to kill another user
/rob @user - Rob another user
/protect level - Buy protection
/revive - Revive after death

*🛍️ SHOP COMMANDS:*
/items - View shop items
/buy item_id - Buy an item
/sell item_id - Sell your item
/price item_id amount - Check price
/setprice item_id amount - Set item price

*💝 RELATIONSHIP COMMANDS:*
/couples - View couples
/marry @user - Propose to user
/divorce - Divorce your partner

*🎮 GAME COMMANDS:*
/bomb amount - Start bomb game
/wordgame amount - Start word game
/spin - Spin the wheel

*🛡️ ADMIN COMMANDS:*
/warn @user - Warn a user
/kick @user - Kick from group
/ban @user - Ban from group
/unban user_id - Unban user
/mute @user - Mute user
/unmute @user - Unmute user

*📊 INFO COMMANDS:*
/look @user - Look at user's profile
/brain - Test your brain
/book - Read a book quote

/help - Show this message
            """
    await safe_reply(update, help_text, parse_mode=ParseMode.MARKDOWN)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user profile"""
    try:
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            user = db.get_or_create_user(user_id, update.effective_user.username)
        
        rank = db.get_user_rank(user_id)
        couple_info = db.get_couple(user_id)
        couple_text = f"💑 Partner: User {couple_info.user2_id if couple_info.user1_id == user_id else couple_info.user1_id}" if couple_info else "💑 Single"
        
        profile_text = f"""
📊 *PROFILE - {user.first_name}*

💰 Balance: {format_money(user.balance)}
🏦 Bank: {format_money(user.bank_balance)}
📈 Level: {user.level}
⭐ Experience: {user.experience}
🏆 Rank: #{rank or 'N/A'}

⚔️ Kills: {user.kills}
💀 Deaths: {user.deaths}
⏰ Status: {'🛡️ Protected' if user.is_protected else '❌ Vulnerable'}

{couple_text}
⚠️ Warnings: {user.warning_count}
🔇 Status: {'🤐 Muted' if user.is_muted else '✅ Active'}
        """
        
        await safe_reply(update, profile_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        await update.message.reply_text("❌ Error loading profile")

@rate_limit(requests=30, window=60)
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check balance"""
    try:
        user_id = update.effective_user.id
        user = db.get_or_create_user(user_id, update.effective_user.username)
        
        text = f"""
💰 *BALANCE - {user.first_name}*

💵 Hand: {format_money(user.balance)}
🏦 Bank: {format_money(user.bank_balance)}
💎 Total: {format_money(user.balance + user.bank_balance)}
        """
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in balance_command: {e}")
        await update.message.reply_text("❌ Error checking balance")

@rate_limit(requests=20, window=60)
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily reward"""
    try:
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            user = db.get_or_create_user(user_id, update.effective_user.username)
        
        now = datetime.now().timestamp()
        if user.last_daily_time and (now - user.last_daily_time) < 86400:  # 24 hours
            remaining = int(86400 - (now - user.last_daily_time))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await update.message.reply_text(f"⏰ Come back in {hours}h {minutes}m for your daily reward!")
            return
        
        bonus = settings.BOT_SETTINGS['daily_bonus_base']
        db.add_balance(user_id, bonus)
        db.update_user(user_id, last_daily_time=now)
        
        await update.message.reply_text(
            f"✅ *DAILY REWARD!*\n\n💰 You received {format_money(bonus)}!",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in daily_command: {e}")
        await update.message.reply_text("❌ Error claiming daily reward")

@rate_limit(requests=10, window=60)
async def work_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Work for money"""
    try:
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user:
            user = db.get_or_create_user(user_id, update.effective_user.username)
        
        now = datetime.now().timestamp()
        if user.last_work_time and (now - user.last_work_time) < 3600:  # 1 hour
            remaining = int(3600 - (now - user.last_work_time))
            await update.message.reply_text(f"😴 You're tired! Work again in {remaining}s")
            return
        
        min_work = settings.BOT_SETTINGS['work_min']
        max_work = settings.BOT_SETTINGS['work_max']
        earned = random.randint(min_work, max_work)
        
        db.add_balance(user_id, earned)
        db.update_user(user_id, last_work_time=now)
        
        jobs = ["💼 Sold newspapers", "🔧 Fixed computers", "🍕 Delivered pizza", "🏠 Cleaned houses", "💻 Did freelance"]
        job = random.choice(jobs)
        
        await update.message.reply_text(
            f"""💼 *WORK SESSION COMPLETE!*

{job}

💰 Earned: {format_money(earned)}
⏰ Next work: in 60 minutes
            """,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in work_command: {e}")
        await update.message.reply_text("❌ Error working")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top users leaderboard"""
    try:
        field = "balance"
        if context.args:
            field = context.args[0].lower()
            if field not in ["balance", "level", "experience", "kills"]:
                field = "balance"
        
        top_users = db.get_top_users(field=field, limit=10)
        
        text = f"🏆 *TOP 10 BY {field.upper()}*\n\n"
        for i, user in enumerate(top_users, 1):
            value = getattr(user, field)
            text += f"{i}. @{user.username or f'User{user.id}'} - {value:,}\n"
        
        await safe_reply(update, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in top_command: {e}")
        await update.message.reply_text("❌ Error loading leaderboard")

@rate_limit(requests=5, window=60)
async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill another user"""
    try:
        await update.message.send_chat_action(ChatAction.TYPING)
        
        if not context.args:
            await update.message.reply_text("Usage: /kill @username")
            return
        
        killer_id = update.effective_user.id
        target_username = context.args[0].replace("@", "")
        
        result = await game_mgr.kill_user(killer_id, target_username)
        
        if result['success']:
            await safe_reply(update, result['message'], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    except Exception as e:
        logger.error(f"Error in kill_command: {e}")
        await update.message.reply_text("❌ Error executing kill")

@rate_limit(requests=5, window=60)
async def rob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rob another user"""
    try:
        await update.message.send_chat_action(ChatAction.TYPING)
        
        if not context.args:
            await update.message.reply_text("Usage: /rob @username")
            return
        
        robber_id = update.effective_user.id
        target_username = context.args[0].replace("@", "")
        
        result = await game_mgr.rob_user(robber_id, target_username)
        
        if result['success']:
            await safe_reply(update, result['message'], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ {result['message']}")
    except Exception as e:
        logger.error(f"Error in rob_command: {e}")
        await update.message.reply_text("❌ Error executing rob")

async def protect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy protection"""
    try:
        if not context.args:
            prices = settings.BOT_SETTINGS['protection_prices']
            text = "🛡️ *PROTECTION LEVELS:*\n\n"
            for level, price in prices.items():
                text += f"Level {level}: {format_money(price)}\n"
            text += "\nUsage: /protect level"
            await safe_reply(update, text, parse_mode=ParseMode.MARKDOWN)
            return
        
        user_id = update.effective_user.id
        try:
            level = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid protection level")
            return
        
        result = await game_mgr.buy_protection(user_id, level)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in protect_command: {e}")
        await update.message.reply_text("❌ Error buying protection")

async def revive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Revive after death"""
    try:
        user_id = update.effective_user.id
        result = await game_mgr.revive_user(user_id)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in revive_command: {e}")
        await update.message.reply_text("❌ Error reviving")

async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give money to another user"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /give @username amount")
            return
        
        giver_id = update.effective_user.id
        target_username = context.args[0].replace("@", "")
        
        try:
            amount = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        result = await economy_mgr.give_money(giver_id, target_username, amount)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in give_command: {e}")
        await update.message.reply_text("❌ Error giving money")

async def items_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View shop items"""
    try:
        page = 1
        if context.args:
            try:
                page = int(context.args[0])
            except ValueError:
                page = 1
        
        items_per_page = settings.BOT_SETTINGS['max_items_per_page']
        offset = (page - 1) * items_per_page
        
        items = db.get_items(limit=items_per_page, offset=offset)
        
        text = f"🛍️ *SHOP - PAGE {page}*\n\n"
        for item in items:
            text += f"*{item.emoji} {item.name}* - {format_money(item.price)}\n{item.description}\n\n"
        
        text += f"Use: /buy item_id"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in items_command: {e}")
        await update.message.reply_text("❌ Error loading items")

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy an item"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /buy item_id")
            return
        
        user_id = update.effective_user.id
        try:
            item_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid item ID")
            return
        
        result = await economy_mgr.buy_item(user_id, item_id)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in buy_command: {e}")
        await update.message.reply_text("❌ Error buying item")

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sell an item"""
    await update.message.reply_text("🏪 Sell command coming soon!")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check item price"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /price item_id")
            return
        
        try:
            item_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid item ID")
            return
        
        item = db.get_item(item_id)
        if not item:
            await update.message.reply_text("❌ Item not found")
            return
        
        await update.message.reply_text(
            f"""
{item.emoji} *{item.name}*

💰 Price: {format_money(item.price)}
📝 Description: {item.description}

/buy {item.id} - Buy this item
            """,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in price_command: {e}")
        await update.message.reply_text("❌ Error checking price")

@validate_owner
async def setprice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner command: Set item price"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /setprice item_id new_price")
            return
        
        try:
            item_id = int(context.args[0])
            new_price = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid item ID or price")
            return
        
        item = db.get_item(item_id)
        if not item:
            await update.message.reply_text("❌ Item not found")
            return
        
        # Update in database (you'd need to implement this)
        await update.message.reply_text(
            f"✅ Price updated: {item.emoji} {item.name} - {format_money(new_price)}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in setprice_command: {e}")
        await update.message.reply_text("❌ Error setting price")

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deposit to bank"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /deposit amount")
            return
        
        user_id = update.effective_user.id
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        result = await economy_mgr.deposit(user_id, amount)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in deposit_command: {e}")
        await update.message.reply_text("❌ Error depositing")

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Withdraw from bank"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /withdraw amount")
            return
        
        user_id = update.effective_user.id
        try:
            amount = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        result = await economy_mgr.withdraw(user_id, amount)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in withdraw_command: {e}")
        await update.message.reply_text("❌ Error withdrawing")

async def couples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View couples"""
    try:
        user_id = update.effective_user.id
        couple = db.get_couple(user_id)
        
        if not couple:
            await update.message.reply_text("💑 You're not in a couple yet!")
            return
        
        partner_id = couple.user2_id if couple.user1_id == user_id else couple.user1_id
        partner = db.get_user(partner_id)
        
        days_together = int((datetime.now().timestamp() - couple.couple_since) / 86400)
        
        await update.message.reply_text(
            f"""
💑 *YOUR RELATIONSHIP*

Partner: @{partner.username or f'User{partner.id}'}
Days Together: {days_together} 📅
Couple Since: {datetime.fromtimestamp(couple.couple_since).strftime('%Y-%m-%d')}
            """,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in couples_command: {e}")
        await update.message.reply_text("❌ Error loading couples")

@validate_admin
async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick user from group"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /kick @username")
            return
        
        await update.message.reply_text("Kick functionality requires group admin access")
    except Exception as e:
        logger.error(f"Error in kick_command: {e}")
        await update.message.reply_text("❌ Error kicking user")

@validate_admin
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban user from group"""
    await update.message.reply_text("Ban command available in groups")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban user"""
    await update.message.reply_text("Unban command available in groups")

@validate_admin
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute user"""
    await update.message.reply_text("Mute command available in groups")

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unmute user"""
    await update.message.reply_text("Unmute command available in groups")

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn user"""
    try:
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /warn @username reason")
            return
        
        target = context.args[0].replace("@", "")
        reason = " ".join(context.args[1:])
        
        result = await mod_mgr.warn_user(update.effective_user.id, target, reason)
        await update.message.reply_text(result['message'], parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in warn_command: {e}")
        await update.message.reply_text("❌ Error warning user")

async def look_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Look at user profile"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /look @username")
            return
        
        username = context.args[0].replace("@", "")
        # Look up user by username
        await update.message.reply_text(f"🔍 Looking at @{username}'s profile...")
    except Exception as e:
        logger.error(f"Error in look_command: {e}")
        await update.message.reply_text("❌ Error looking up user")

async def brain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test your brain"""
    questions = [
        "What's 2+2?",
        "What's the capital of France?",
        "How many continents are there?",
    ]
    await update.message.reply_text(f"🧠 {random.choice(questions)}")

async def book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Read a book quote"""
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Life is what happens when you're busy making other plans. - John Lennon",
    ]
    await update.message.reply_text(f"📚 *Quote of the moment:*\n\n_{random.choice(quotes)}_", parse_mode=ParseMode.MARKDOWN)

async def bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start bomb game"""
    try:
        if update.effective_chat.type == "private":
            await update.message.reply_text("🎮 Games work in groups only!")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /bomb amount")
            return
        
        try:
            entry_fee = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
        
        await update.message.reply_text("💣 Bomb game started! Use /join 💣 to join")
    except Exception as e:
        logger.error(f"Error in bomb_command: {e}")
        await update.message.reply_text("❌ Error starting game")

async def wordgame_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start wordgame"""
    try:
        if update.effective_chat.type == "private":
            await update.message.reply_text("🎮 Games work in groups only!")
            return
        
        await update.message.reply_text("🔤 Word game started!")
    except Exception as e:
        logger.error(f"Error in wordgame_command: {e}")
        await update.message.reply_text("❌ Error starting game")

async def spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Spin the wheel"""
    try:
        await update.message.reply_text("🎡 You spun the wheel!\n\n" + "🎁 " * random.randint(1, 5))
    except Exception as e:
        logger.error(f"Error in spin_command: {e}")
        await update.message.reply_text("❌ Error spinning wheel")
