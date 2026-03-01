import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from flask import Flask
import threading

# Import the scraping function from our scraper module
from scraper import scrape_google_maps

# Load environment variables
load_dotenv()

# Configure Logging for the bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "isi_di_sini":
    logger.error("TELEGRAM_BOT_TOKEN is not set properly in .env file.")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Halo! Saya adalah bot Google Maps Scraper untuk Airtable.\n\n"
        "Anda bisa mengetik perintah manual, contoh:\n"
        "🔍 `/scrape kedai kopi di Jakarta Selatan`\n\n"
        "Atau, pilih salah satu pencarian cepat di bawah ini:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("☕ Kedai Kopi di Jaksel", callback_data="scrape_kopi"),
            InlineKeyboardButton("🧺 Laundry di Bandung", callback_data="scrape_laundry")
        ],
        [
            InlineKeyboardButton("💇 Salon di Surabaya", callback_data="scrape_salon"),
            InlineKeyboardButton("🛠️ Bengkel di Jogja", callback_data="scrape_bengkel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use reply_text instead of reply_markdown if using MarkdownV2 is tricky with special characters
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()

    # Determine keyword and location based on callback_data
    if query.data == "scrape_kopi":
        keyword, location = "kedai kopi", "Jakarta Selatan"
    elif query.data == "scrape_laundry":
        keyword, location = "laundry", "Bandung"
    elif query.data == "scrape_salon":
        keyword, location = "salon", "Surabaya"
    elif query.data == "scrape_bengkel":
        keyword, location = "bengkel mobil", "Yogyakarta"
    else:
        return

    await query.edit_message_text(text=f"⏳ Memulai pencarian untuk '{keyword.title()}' di '{location.title()}' dari tombol...\nMohon bersabar 1-2 menit.")
    
    try:
        logger.info(f"User requested scrape via button: {keyword} in {location}")
        # Run scraper (10 results)
        await asyncio.to_thread(scrape_google_maps, keyword=keyword, location=location, max_results=10)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"✅ Scraping SELESAI untuk '{keyword.title()}' di '{location.title()}'.\nSilakan cek tabel Airtable Anda!"
        )
    except Exception as e:
        logger.error(f"Error during scrape button command: {e}", exc_info=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Terjadi kesalahan:\n{str(e)[:200]}...")


import asyncio

# ... (other imports remain as they are, but add asyncio at top)

async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (the beginning of scrape_command remains unchanged)
    # Just grab the keyword and location:
    user_input = " ".join(context.args)
    
    if not user_input or " di " not in user_input.lower():
        await update.message.reply_text(
            "⚠️ Format perintah salah.\n"
            "Gunakan format: /scrape [keyword] di [lokasi]\n"
            "Contoh: /scrape sate madura di Bandung"
        )
        return

    try:
        parts = user_input.lower().split(" di ", 1)
        keyword = parts[0].strip()
        location = parts[1].strip()
        
        if not keyword or not location:
            raise ValueError("Keyword atau lokasi kosong.")
            
    except Exception as e:
        await update.message.reply_text("⚠️ Gagal mengekstrak keyword dan lokasi. Pastikan formatnya benar.")
        return

    await update.message.reply_text(f"⏳ Bot sedang memproses pencarian '{keyword.title()}' di '{location.title()}'...\nMohon bersabar, ini akan memakan waktu 1-2 menit.")
    
    try:
        logger.info(f"User requested scrape: {keyword} in {location}")
        
        # PENTING: Jalankan fungsi sinkronis (Playwright_sync API) di thread terpisah 
        # agar tidak bentrok dengan asyncio loop bawaan python-telegram-bot
        await asyncio.to_thread(scrape_google_maps, keyword=keyword, location=location, max_results=10)
        
        await update.message.reply_text(f"✅ Scraping SELESAI untuk '{keyword.title()}' di '{location.title()}'.\nSilakan cek tabel Airtable Anda!")
        
    except Exception as e:
        logger.error(f"Error during scrape command: {e}", exc_info=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Terjadi kesalahan:\n{str(e)[:200]}...")


# ==========================================
# DUMMY WEB SERVER (Untuk Hosting Gratis)
# ==========================================
# Hosting seperti Hugging Face / Render mewajibkan aplikasi membuka sebuah "Port Website"
# Jika tidak ada Port yang terbuka, server akan mengira aplikasi kita error/mati.
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Google Maps Scraper Bot is Running!"

def run_web():
    # Gunakan port 7860 untuk Hugging Face, atau ambil dari variabel PORT (Render/Heroku)
    port = int(os.environ.get("PORT", 7860))
    app_web.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Menjalankan Web Server di latar belakang
    threading.Thread(target=run_web, daemon=True).start()
    
    print("="*50)
    print("TELEGRAM BOT SEDANG BERJALAN...")
    print("Tekan Ctrl+C untuk menghentikan bot.")
    print("="*50)
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scrape", scrape_command))
    app.add_handler(CallbackQueryHandler(button_click))

    # Run the bot until the user presses Ctrl-C
    app.run_polling()
