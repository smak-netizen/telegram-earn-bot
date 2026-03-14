import random
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
from apscheduler.schedulers.background import BackgroundScheduler

# ===== CONFIG =====
BOT_TOKEN = "8763245430:AAH5_a92NbMo_dP5RwS1mBbiLFe8B4HXx7E"
ADMIN_ID = 8389153247
MIN_WITHDRAWAL = 5     # Minimum withdrawal in $DOGE
DOGE_PRICE = 0.10      # For display/conversion purposes
DAILY_BONUS = 0.01     # Daily login reward in $DOGE

# ===== DATABASE =====
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    tasks_done INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_daily TEXT,
    banned INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals(
    user_id INTEGER,
    ref_id INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS lucky_draw(
    user_id INTEGER,
    date TEXT
)
""")
conn.commit()

# ===== SHORTLINKS =====
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

# ===== LEVEL TASK LIMITS =====
level_task_limit = {1:12, 2:24, 3:36, 4:48, 5:60}

# ===== MAIN MENU =====
menu = ReplyKeyboardMarkup([
    ["🎯 Start Task", "💰 Balance"],
    ["🎁 Daily Bonus","👥 Invite Friends"],
    ["💳 Withdraw", "🏆 Lucky Draw"],
], resize_keyboard=True)

# ===== HELPERS =====
def get_task_limit(level):
    return level_task_limit.get(level, 12)

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, ref_id=None):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()
    if ref_id:
        cursor.execute("INSERT INTO referrals(user_id, ref_id) VALUES(?,?)", (user_id, ref_id))
        cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (ref_id,))
        conn.commit()

def level_up(user_id):
    cursor.execute("SELECT tasks_done, level FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    tasks, level = data
    new_level = min(5, tasks // 50 + 1)
    if new_level > level:
        cursor.execute("UPDATE users SET level=? WHERE user_id=?", (new_level, user_id))
        conn.commit()
        return True
    return False

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ref_id = None
    args = context.args
    if args:
        try:
            ref_id = int(args[0])
        except:
            pass
        if ref_id == user_id:
            ref_id = None

    add_user(user_id, ref_id)
    await update.message.reply_text(
        "🚀 Welcome, brave achiever! 💪\n"
        "Complete tasks, earn $DOGE rewards, and climb the leaderboard! 📈\n"
        "Remember: small steps daily lead to huge success! 🌟",
        reply_markup=menu
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user[6]==1:
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    bal = user[1]
    await update.message.reply_text(f"💰 Your current balance: ${bal:.2f} DOGE\nKeep completing tasks to level up and earn more! 🚀")

# ===== TASK FLOW =====
async def start_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user[6]==1:
        await update.message.reply_text("❌ You are banned from using tasks.")
        return
    limit = get_task_limit(user[4])
    if user[3]>=limit:
        await update.message.reply_text(f"❌ You reached your daily task limit ({limit}) for your level.\nLevel up to unlock more tasks! 🔓")
        return
    keyboard = [[InlineKeyboardButton("✅ Click here to start task", callback_data="task_clicked")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎯 Ready to earn some $DOGE? 💰\nClick below to start your task! 📌\nStay focused, complete it carefully, and submit the OTP to get your reward! 🌟",
        reply_markup=reply_markup
    )

async def task_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    shortlink = random.choice(shortlinks)
    await query.edit_message_text(
        f"🔗 Here’s your task link:\n{shortlink}\n\n"
        "After completing, come back and send the 6-digit OTP provided at the end of the task to claim your $DOGE reward! 💎\n"
        "You’re doing amazing, keep it up! 🚀🔥"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user[6]==1:
        await update.message.reply_text("❌ You are banned from verifying tasks.")
        return
    if code.isdigit() and len(code)==6:
        reward = 0.02
        cursor.execute("UPDATE users SET balance = balance + ?, tasks_done = tasks_done + 1 WHERE user_id=?", (reward,user_id))
        conn.commit()
        leveled = level_up(user_id)
        msg = f"✅ Task Verified! You earned: ${reward} DOGE 🎉\nKeep going, you’re doing great! 💪"
        if leveled:
            msg += "\n🌟 Congratulations! You’ve leveled up! More tasks unlocked! 🚀"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ Invalid code. Make sure it’s a 6-digit number. Try again! 💡")

# ===== DAILY BONUS =====
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user[6]==1:
        await update.message.reply_text("❌ You are banned from claiming daily bonus.")
        return
    today = str(datetime.now().date())
    if user[5]==today:
        await update.message.reply_text("❌ You already claimed your daily bonus today! ⏳ Come back tomorrow 🌞")
        return
    cursor.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE user_id=?", (DAILY_BONUS,today,user_id))
    conn.commit()
    await update.message.reply_text(f"🎁 Daily Bonus Claimed: ${DAILY_BONUS} DOGE 🌟\nKeep it up! Small steps every day lead to big rewards! 🚀")

# ===== REFERRALS =====
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f"👥 Invite your friends using this link:\n{link}\n\n"
        "You need 2 referrals to unlock withdrawals. 🌟\n"
        "Share and help your friends earn too! 🚀"
    )

# ===== WITHDRAWAL =====
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user[6]==1:
        await update.message.reply_text("❌ You are banned from withdrawals.")
        return
    bal = user[1]
    refs = user[2]
    if refs < 2:
        await update.message.reply_text(f"❌ Withdrawal locked.\nInvite 2 friends first. 👥\nReferrals: {refs}/2")
        return
    if bal < MIN_WITHDRAWAL:
        await update.message.reply_text(f"❌ Minimum withdrawal is ${MIN_WITHDRAWAL} DOGE 💰")
        return
    await update.message.reply_text("💳 Enter your DOGE wallet address to receive your payment. 🌟 Good luck!")

# ===== LUCKY DRAW =====
scheduler = BackgroundScheduler()
def lucky_draw():
    today = str(datetime.now().date())
    cursor.execute("DELETE FROM lucky_draw WHERE date=?", (today,))
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    winners = cursor.fetchall()
    for user in winners:
        cursor.execute("INSERT INTO lucky_draw(user_id, date) VALUES(?,?)", (user[0], today))
    conn.commit()
scheduler.add_job(lucky_draw, 'cron', hour=0, minute=0)
scheduler.start()

async def lucky_draw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = str(datetime.now().date())
    cursor.execute("SELECT user_id FROM lucky_draw WHERE date=?", (today,))
    winners = cursor.fetchall()
    if not winners:
        await update.message.reply_text("No winners yet today. Wait for midnight! ⏰")
        return
    msg = "🏆 Lucky Draw Winners Today:\n"
    for i, w in enumerate(winners,1):
        msg += f"{i}. User ID: {w[0]}\n"
    await update.message.reply_text(msg)

# ===== LEADERBOARD =====
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()
    msg = "📊 Top Earners:\n"
    for i,u in enumerate(users,1):
        msg += f"{i}. User ID: {u[0]} — ${u[1]:.2f} DOGE 💎\n"
    await update.message.reply_text(msg)

# ===== ADMIN COMMANDS =====
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    await update.message.reply_text(f"👥 Total Users: {total} 🚀")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = " ".join(context.args)
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    for u in users:
        try:
            await context.bot.send_message(u[0], text)
        except:
            pass
    await update.message.reply_text("📢 Broadcast sent to all users!")

# ===== APPLICATION =====
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("💰 Balance"), balance))
app.add_handler(MessageHandler(filters.Regex("🎯 Start Task"), start_task))
app.add_handler(CallbackQueryHandler(task_button, pattern="task_clicked"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))
app.add_handler(MessageHandler(filters.Regex("🎁 Daily Bonus"), daily_bonus))
app.add_handler(MessageHandler(filters.Regex("👥 Invite Friends"), invite))
app.add_handler(MessageHandler(filters.Regex("💳 Withdraw"), withdraw))
app.add_handler(MessageHandler(filters.Regex("🏆 Lucky Draw"), lucky_draw_cmd))
app.add_handler(MessageHandler(filters.Regex("📊 Leaderboard"), leaderboard))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))

print("Bot started successfully! 🚀")
app.run_polling()
