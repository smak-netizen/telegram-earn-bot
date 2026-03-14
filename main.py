import random
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8763245430:AAH5_a92NbMo_dP5RwS1mBbiLFe8B4HXx7E"
ADMIN_ID = 8389153247

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    tasks_done INTEGER DEFAULT 0
)
""")

conn.commit()

shortlinks = [
    "https://shrinkme.click/shrme",
    "https://ouo.io/jslW3g",
    "https://tpi.li/shrnkearn",
    "https://oii.la/clksh0001",
    "https://shrtslug.biz/8LsPH",
    "https://mitly.us/ByBS",
    "https://exe.io/exeio123",
    "https://sfl.gl/SVhak",
    "https://gplinks.co/gplnk0001",
    "https://cuty.io/cuty0001",
    "https://fc-lc.xyz/fclc0001",
    "https://linkjust.com/linkjust0001"
]

menu = ReplyKeyboardMarkup(
[
["🎯 Start Task","📋 Submit Code"],
["💰 Balance","💳 Withdraw"]
],
resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)",(user_id,))
        conn.commit()

    await update.message.reply_text(
        "🚀 Welcome!\nEarn rewards by completing tasks.",
        reply_markup=menu
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?",(user_id,))
    bal = cursor.fetchone()[0]

    await update.message.reply_text(f"💰 Balance: ${bal:.2f} DOGE")

async def start_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = random.choice(shortlinks)

    await update.message.reply_text(
        f"🎯 Complete this task:\n\n{link}\n\nAfter finishing send the 6 digit code."
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text

    if code.isdigit() and len(code) == 6:

        reward = 0.02
        user_id = update.effective_user.id

        cursor.execute(
        "UPDATE users SET balance = balance + ?, tasks_done = tasks_done + 1 WHERE user_id=?",
        (reward,user_id)
        )
        conn.commit()

        await update.message.reply_text(
        f"✅ Task Verified\nReward: ${reward} DOGE"
        )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute("SELECT balance FROM users WHERE user_id=?",(user_id,))
    balance = cursor.fetchone()[0]

    if balance < 5:
        await update.message.reply_text("Minimum withdrawal is $5")
        return

    await update.message.reply_text(
    "Send your DOGE wallet address."
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("💰 Balance"), balance))
app.add_handler(MessageHandler(filters.Regex("🎯 Start Task"), start_task))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))
app.add_handler(MessageHandler(filters.Regex("💳 Withdraw"), withdraw))

app.run_polling()
