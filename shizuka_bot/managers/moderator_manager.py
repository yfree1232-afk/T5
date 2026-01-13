"""Moderator manager - Moderation and admin functions"""
import logging
from datetime import datetime, timedelta
from shizuka_bot.database import DatabaseManager

logger = logging.getLogger(__name__)
db = DatabaseManager()

class ModeratorManager:
    """Manages moderation operations: warn, mute, ban, kick"""
    
    @staticmethod
    async def warn_user(admin_id: int, target_username: str, reason: str) -> dict:
        """Warn a user"""
        try:
            # Find target
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (target_username,))
                target_row = cursor.fetchone()
            
            if not target_row:
                return {"success": False, "message": f"❌ User @{target_username} not found"}
            
            target = db._row_to_user(target_row)
            
            # Add warning
            db.add_warning(target.id, reason, admin_id)
            
            return {
                "success": True,
                "message": f"""
⚠️ *WARNING ISSUED!* ⚠️

User: @{target_username}
Reason: {reason}
Total Warnings: {target.warning_count + 1}
                """
            }
        except Exception as e:
            logger.error(f"Warn error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def mute_user(user_id: int, duration_minutes: int = 60) -> dict:
        """Mute a user temporarily"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ User not found"}
            
            mute_end_time = datetime.now().timestamp() + (duration_minutes * 60)
            
            db.update_user(user_id, is_muted=True, mute_end_time=mute_end_time)
            
            return {
                "success": True,
                "message": f"""
🔇 *USER MUTED!* 🔇

Duration: {duration_minutes} minutes
Mute Ends: {datetime.fromtimestamp(mute_end_time).strftime('%H:%M')}
                """
            }
        except Exception as e:
            logger.error(f"Mute error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def unmute_user(user_id: int) -> dict:
        """Unmute a user"""
        try:
            db.update_user(user_id, is_muted=False, mute_end_time=None)
            
            return {
                "success": True,
                "message": "✅ User unmuted!"
            }
        except Exception as e:
            logger.error(f"Unmute error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def ban_user(user_id: int, reason: str = "No reason") -> dict:
        """Ban a user"""
        try:
            db.update_user(user_id, is_banned=True, ban_reason=reason)
            
            return {
                "success": True,
                "message": f"""
🚫 *USER BANNED!* 🚫

Reason: {reason}
                """
            }
        except Exception as e:
            logger.error(f"Ban error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def unban_user(user_id: int) -> dict:
        """Unban a user"""
        try:
            db.update_user(user_id, is_banned=False, ban_reason=None)
            
            return {
                "success": True,
                "message": "✅ User unbanned!"
            }
        except Exception as e:
            logger.error(f"Unban error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
