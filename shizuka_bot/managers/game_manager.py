"""Game manager - All game-related logic"""
import logging
import random
from datetime import datetime, timedelta
from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager

logger = logging.getLogger(__name__)
db = DatabaseManager()

class GameManager:
    """Manages all game operations: kill, rob, protect, etc."""
    
    @staticmethod
    async def kill_user(killer_id: int, target_username: str) -> dict:
        """Kill another user with success/fail logic"""
        try:
            killer = db.get_user(killer_id)
            if not killer:
                return {"success": False, "message": "❌ Your profile not found"}
            
            kill_cost = settings.BOT_SETTINGS['kill_cost']
            if killer.balance < kill_cost:
                return {"success": False, "message": f"❌ Insufficient balance. Need {kill_cost}💵"}
            
            # Find target
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (target_username,))
                target_row = cursor.fetchone()
            
            if not target_row:
                return {"success": False, "message": f"❌ User @{target_username} not found"}
            
            target = db._row_to_user(target_row)
            
            # Check protection
            now = datetime.now().timestamp()
            if target.is_protected and target.protection_end_time and target.protection_end_time > now:
                return {"success": False, "message": f"🛡️ {target_username} is protected! Try again later."}
            
            # Calculate success rate
            success_rate = settings.BOT_SETTINGS['kill_success_rate']
            is_success = random.randint(1, 100) <= success_rate
            
            if is_success:
                # Kill successful
                db.add_balance(killer_id, -kill_cost)
                db.update_user(killer_id, kills=killer.kills + 1)
                db.update_user(target.id, deaths=target.deaths + 1)
                
                reward = kill_cost * 2
                db.add_balance(killer_id, reward)
                
                return {
                    "success": True,
                    "message": f"""
⚔️ *KILL SUCCESSFUL!* ⚔️

🎯 Target: @{target_username}
💰 Reward: +{reward}💵
💀 Kills: {killer.kills + 1}
                    """
                }
            else:
                # Kill failed
                db.add_balance(killer_id, -kill_cost)
                fail_penalty = int(kill_cost * 0.5)
                db.add_balance(target.id, fail_penalty)
                
                cooldown = settings.BOT_SETTINGS['kill_fail_cooldown']
                
                return {
                    "success": True,
                    "message": f"""
❌ *KILL FAILED!* ❌

🎯 Target: @{target_username}
💸 Loss: {kill_cost}💵
💰 Target got: +{fail_penalty}💵
⏰ Cooldown: {cooldown}s
                    """
                }
        except Exception as e:
            logger.error(f"Kill error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def rob_user(robber_id: int, target_username: str) -> dict:
        """Rob another user"""
        try:
            robber = db.get_user(robber_id)
            if not robber:
                return {"success": False, "message": "❌ Your profile not found"}
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (target_username,))
                target_row = cursor.fetchone()
            
            if not target_row:
                return {"success": False, "message": f"❌ User @{target_username} not found"}
            
            target = db._row_to_user(target_row)
            
            # Check last rob time
            now = datetime.now().timestamp()
            rob_cooldown = settings.BOT_SETTINGS['rob_cooldown']
            
            if robber.last_rob_time and (now - robber.last_rob_time) < rob_cooldown:
                remaining = int(rob_cooldown - (now - robber.last_rob_time))
                return {"success": False, "message": f"⏰ Rob cooldown! Try again in {remaining}s"}
            
            success_rate = settings.BOT_SETTINGS['rob_success_rate']
            is_success = random.randint(1, 100) <= success_rate
            
            if is_success:
                # Rob successful
                rob_amount = random.randint(int(target.balance * 0.1), int(target.balance * 0.3))
                db.add_balance(robber_id, rob_amount)
                db.add_balance(target.id, -rob_amount)
                db.update_user(robber_id, last_rob_time=now)
                
                return {
                    "success": True,
                    "message": f"""
💰 *ROB SUCCESSFUL!* 💰

👊 Target: @{target_username}
💵 Stolen: {rob_amount}💵
                    """
                }
            else:
                # Rob failed
                fail_penalty = random.randint(100, 500)
                db.add_balance(robber_id, -fail_penalty)
                db.update_user(robber_id, last_rob_time=now)
                
                return {
                    "success": True,
                    "message": f"""
❌ *ROB FAILED!* ❌

🚔 Got caught!
💸 Fine: {fail_penalty}💵
                    """
                }
        except Exception as e:
            logger.error(f"Rob error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def buy_protection(user_id: int, level: int) -> dict:
        """Buy protection for user"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ Your profile not found"}
            
            protection_prices = settings.BOT_SETTINGS['protection_prices']
            
            if level not in protection_prices:
                levels = list(protection_prices.keys())
                return {"success": False, "message": f"❌ Available levels: {levels}"}
            
            price = protection_prices[level]
            duration_hours = level * 4  # Level 1 = 4 hours, Level 2 = 8 hours, etc.
            
            if user.balance < price:
                return {"success": False, "message": f"❌ Insufficient balance. Need {price}💵"}
            
            protection_end = datetime.now().timestamp() + (duration_hours * 3600)
            
            db.add_balance(user_id, -price)
            db.update_user(user_id, is_protected=True, protection_end_time=protection_end)
            
            return {
                "success": True,
                "message": f"""
🛡️ *PROTECTION PURCHASED!* 🛡️

Level: {level}
Duration: {duration_hours} hours
Cost: {price}💵
Ends: {datetime.fromtimestamp(protection_end).strftime('%Y-%m-%d %H:%M')}
                """
            }
        except Exception as e:
            logger.error(f"Protection error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def revive_user(user_id: int) -> dict:
        """Revive user after death"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ Your profile not found"}
            
            if user.deaths == 0:
                return {"success": False, "message": "✅ You're already alive!"}
            
            revive_cost = settings.BOT_SETTINGS['revive_cost']
            
            if user.balance < revive_cost:
                return {"success": False, "message": f"❌ Insufficient balance. Need {revive_cost}💵"}
            
            db.add_balance(user_id, -revive_cost)
            db.update_user(user_id, deaths=0)
            
            return {
                "success": True,
                "message": f"""
✨ *REVIVED!* ✨

Cost: {revive_cost}💵
Status: ✅ Alive
                """
            }
        except Exception as e:
            logger.error(f"Revive error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
