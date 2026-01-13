"""Economy manager - Banking, items, money transactions"""
import logging
from shizuka_bot.config import settings
from shizuka_bot.database import DatabaseManager

logger = logging.getLogger(__name__)
db = DatabaseManager()

class EconomyManager:
    """Manages economy operations: deposit, withdraw, buy, sell, gift"""
    
    @staticmethod
    async def deposit(user_id: int, amount: int) -> dict:
        """Deposit money to bank"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ Your profile not found"}
            
            min_deposit = settings.BOT_SETTINGS['min_deposit']
            
            if amount < min_deposit:
                return {"success": False, "message": f"❌ Minimum deposit is {min_deposit}💵"}
            
            if user.balance < amount:
                return {"success": False, "message": "❌ Insufficient balance"}
            
            # Calculate fee
            fee = settings.BOT_SETTINGS.get('bank_deposit_fee', 1)
            total_debit = amount + fee
            
            if user.balance < total_debit:
                return {"success": False, "message": f"❌ Need {total_debit}💵 (including {fee}💵 fee)"}
            
            db.add_balance(user_id, -total_debit)
            db.add_bank_balance(user_id, amount)
            
            return {
                "success": True,
                "message": f"""
🏦 *DEPOSIT SUCCESSFUL!* 🏦

💵 Amount: {amount}💵
💸 Fee: {fee}💵
💼 Bank Balance: {user.bank_balance + amount}💵
                """
            }
        except Exception as e:
            logger.error(f"Deposit error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def withdraw(user_id: int, amount: int) -> dict:
        """Withdraw money from bank"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ Your profile not found"}
            
            min_withdraw = settings.BOT_SETTINGS['min_withdraw']
            
            if amount < min_withdraw:
                return {"success": False, "message": f"❌ Minimum withdrawal is {min_withdraw}💵"}
            
            if user.bank_balance < amount:
                return {"success": False, "message": "❌ Insufficient bank balance"}
            
            # Calculate fee
            fee = settings.BOT_SETTINGS.get('bank_withdraw_fee', 2)
            total_debit = amount + fee
            
            if user.bank_balance < total_debit:
                return {"success": False, "message": f"❌ Need {total_debit}💵 (including {fee}💵 fee)"}
            
            db.add_bank_balance(user_id, -total_debit)
            db.add_balance(user_id, amount)
            
            return {
                "success": True,
                "message": f"""
🏦 *WITHDRAWAL SUCCESSFUL!* 🏦

💵 Amount: {amount}💵
💸 Fee: {fee}💵
💼 Bank Balance: {user.bank_balance - total_debit}💵
                """
            }
        except Exception as e:
            logger.error(f"Withdraw error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def give_money(giver_id: int, target_username: str, amount: int) -> dict:
        """Give money to another user"""
        try:
            giver = db.get_user(giver_id)
            if not giver:
                return {"success": False, "message": "❌ Your profile not found"}
            
            if amount <= 0:
                return {"success": False, "message": "❌ Amount must be positive"}
            
            if giver.balance < amount:
                return {"success": False, "message": "❌ Insufficient balance"}
            
            # Find target
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (target_username,))
                target_row = cursor.fetchone()
            
            if not target_row:
                return {"success": False, "message": f"❌ User @{target_username} not found"}
            
            target = db._row_to_user(target_row)
            
            # Calculate tax
            tax_rate = settings.BOT_SETTINGS.get('tax_rate', 10) / 100
            tax = int(amount * tax_rate)
            net_amount = amount - tax
            
            db.add_balance(giver_id, -amount)
            db.add_balance(target.id, net_amount)
            
            return {
                "success": True,
                "message": f"""
💝 *MONEY SENT!* 💝

Recipient: @{target_username}
Amount: {net_amount}💵
Tax: {tax}💵
                """
            }
        except Exception as e:
            logger.error(f"Give money error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
    
    @staticmethod
    async def buy_item(user_id: int, item_id: int) -> dict:
        """Buy item from shop"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {"success": False, "message": "❌ Your profile not found"}
            
            item = db.get_item(item_id)
            if not item:
                return {"success": False, "message": "❌ Item not found"}
            
            if user.balance < item.price:
                return {"success": False, "message": f"❌ Insufficient balance. Need {item.price}💵"}
            
            db.add_balance(user_id, -item.price)
            
            return {
                "success": True,
                "message": f"""
🎁 *ITEM PURCHASED!* 🎁

Item: {item.emoji} {item.name}
Price: {item.price}💵
Remaining Balance: {user.balance - item.price}💵

Use /give @username to gift this item!
                """
            }
        except Exception as e:
            logger.error(f"Buy item error: {e}")
            return {"success": False, "message": f"❌ Error: {str(e)}"}
