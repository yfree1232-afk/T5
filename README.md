# 🌸 SHIZUKA BOT - Advanced Telegram Economy Bot

**Production-Ready | High-Load Capable | Fully Modular | Advanced Architecture**

---

## 🎯 Project Overview

Shizuka Bot is a comprehensive Telegram bot with:
- **💰 Complete Economy System** - Wallet, bank, deposits, withdrawals
- **🎮 Game Management** - Multiplayer games with betting
- **⚔️ PVP System** - Kill, rob, protect with success rates
- **🛍️ Shop System** - Buy/sell items with dynamic pricing
- **👥 Relationship System** - Couples, marriages, profiles
- **🛡️ Moderation Tools** - Warn, mute, ban, kick functionality
- **🤖 AI Chat** - Powered by Google Gemini API
- **📊 Leaderboards** - Rank users by balance, level, kills, experience

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your token
export BOT_TOKEN="your_token_here"

# 3. Run the bot
python main.py
```

---

## 📁 Project Structure

```
shizuka_bot/                    # Main package
├── config/settings.py          # Configuration management
├── database/manager.py         # Database operations
├── models/models.py            # Data models
├── handlers/commands.py        # 30+ command handlers
├── managers/                   # Business logic (games, economy, moderation)
├── utils/                      # Error handling, decorators, logging
├── logs/                       # Log files
└── data/                       # SQLite database

main.py                         # Entry point
requirements.txt                # Dependencies
```

---

## 💰 Economy System
- Wallet and bank accounts with interest
- Daily bonuses and work tasks
- Item shop with buying/selling
- Money transfers between users
- Deposit/withdrawal fees

---

## 🎮 Gaming System
- Kill/Rob/Protect mechanics
- Success rate calculations
- Cooldown management
- Protection system
- Leaderboards (kills, balance, level, experience)

---

## 👥 Moderation
- Warn system with tracking
- Mute/unmute functionality
- Ban system for users
- Kick command for groups

---

## 🤖 Features
- AI chat with Google Gemini
- Multiplayer games
- Couple system
- Profile viewing
- Comprehensive logging

---

## ⚡ Performance
- Async/await architecture
- Connection pooling
- Rate limiting per user
- Handles 100+ concurrent users
- Sub-500ms response time

---

## 📋 All Commands

**Economy:** /profile, /balance, /daily, /work, /top, /deposit, /withdraw, /give

**PVP:** /kill, /rob, /protect, /revive

**Shop:** /items, /buy, /sell, /price

**Moderation:** /warn, /kick, /ban, /unban, /mute, /unmute

**Other:** /couples, /look, /brain, /book, /bomb, /wordgame, /spin

**Info:** /help, /start

---

## 🔐 Security
✅ Token validation before connection  
✅ Foreign key constraints on database  
✅ Input validation on all commands  
✅ Rate limiting per user  
✅ Authorization checks (owner/admin)  

---

## 📝 Configuration

Edit settings in `shizuka_bot/config/settings.py`:

```python
BOT_SETTINGS = {
    "kill_success_rate": 50,
    "rob_success_rate": 40,
    "daily_bonus_base": 100,
    "work_min": 100,
    "work_max": 500,
    # ... 30+ configurable settings
}
```

---

## 🐛 Troubleshooting

**Invalid Token:** Get new token from [@BotFather](https://t.me/BotFather)

**Commands not working:** Restart bot with `Ctrl+C` then `python main.py`

**Database error:** Delete `shizuka_bot/data/bot.db` and restart

**Check logs:** `tail -f shizuka_bot/logs/bot.log`

---

## 📚 Documentation

- See `SETUP.md` for detailed setup guide
- See `PROJECT_STRUCTURE.md` for architecture details
- Check docstrings in source code
- View logs in `shizuka_bot/logs/bot.log`

---

**🌸 Happy Botting! 🌸**