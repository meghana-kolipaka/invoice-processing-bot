"""Settings read from environment variables so the same code runs on Windows, Linux or in Docker."""
import os

DB_PATH = os.getenv("BOT_DB_PATH", "bot.db")
LOG_DIR = os.getenv("BOT_LOG_DIR", "logs")
REPORT_DIR = os.getenv("BOT_REPORT_DIR", "reports")
ARCHIVE_DIR = os.getenv("BOT_ARCHIVE_DIR", "archive")
INPUT_DIR = os.getenv("BOT_INPUT_DIR", "input")
