# config.py - Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in .env file!")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file!")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dice_bot.db")

# Dice configuration - будет загружаться из dice_meanings.py
# Basic набор: 16 символов
DICE_SET = "basic"  # basic / action / adventure

# AI settings
AI_MODEL = "gpt-3.5-turbo"
AI_TEMPERATURE = 0.8
AI_MAX_TOKENS = 500

# Admin settings
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")  # Telegram IDs через запятую
