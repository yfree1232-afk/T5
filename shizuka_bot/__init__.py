"""Package initialization"""
__version__ = "2.0.0"
__author__ = "Shizuka Bot Developer"
__description__ = "Advanced Telegram Economy Bot with Games, AI Chat, and Moderation"

from shizuka_bot.config import settings, Config
from shizuka_bot.database import DatabaseManager
from shizuka_bot.app import ShizukaBot, main

__all__ = ['ShizukaBot', 'settings', 'Config', 'DatabaseManager', 'main']
