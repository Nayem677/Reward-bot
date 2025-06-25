from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import random
import time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 10
INVITE_REWARD = 2
EARNING_LIMIT = 200

# Simple Arithmetic Questions
simple_questions = [
    ("5 + 7", "12"), ("12 - 3", "9"), ("4 × 6", "24"), ("18 ÷ 3", "6"),
    ("9 + 8", "17"), ("14 - 5", "9"), ("7 × 5", "35"), ("20 ÷ 4", "5"),
    ("6 + 13", "19"), ("11 - 6", "5"), ("3 × 8", "24"), ("24 ÷ 6", "4"),
    ("10 + 15", "25"), ("30 - 12", "18"), ("5 × 9", "45"), ("16 ÷ 4", "4"),
    ("25 + 25", "50"), ("60 - 20", "40"), ("8 × 7", "56"), ("56 ÷ 7", "8")
]

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def get_main_buttons():
    return [
        [InlineKeyboardButton("Home", callback_data="home"), InlineKeyboardButton("Refresh", callback_data="refresh")],
        [InlineKeyboardButton("Invite Friends", callback_data="invite"), InlineKeyboardButton("Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("Chat with Admin", callback_data="admin"), InlineKeyboardButton("Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("Daily Task", callback_data="task"), InlineKeyboardButton("How to Withdraw", callback_data="how")],
        [InlineKeyboardButton("📢 Payment Info", callback_data="notice")]
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    args = context.args

    if user_id not in users:
        users[user_id] = {
            'balance': 5,
            'invites': set(),
            'referred_by': None,
            'last_claimed': 0,
            'task_stage': None,
            'task_answer': None,
            'name': None,
            'used_questions': set(),
            'daily_questions_done': 0,
            'last_task_day': None,
            'watch_earned': False
        }

        if args:
            referrer_id = int(args[0])
            if referrer_id != user_id and referrer_id in users:
                if len(users[referrer_id]['invites']) < MAX_INVITES:
                    if user_id not in users[referrer_id]['invites']:
                        users[user_id]['referred_by'] = referrer_id
                        users[referrer_id]['invites'].add(user_id)
                        users[referrer_id]['balance'] += INVITE_REWARD

    await show_home(update, context)

async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    name = users[user_id].get("name")

    if not name:
        await update.message.reply_text("Type your name:")
        users[user_id]['task_stage'] = "set_name"
        return

    text = f"👤 {name} | 💰 Balance: ${balance:.2f}"
    buttons = get_main_buttons()

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    balance = get_balance(user_id)

    if data in ["home", "refresh"]:
        await show_home(update, context)
        return

    if balance >= EARNING_LIMIT and data.startswith("task"):
        await query.edit_message_text(
            "You have to withdraw your amount now, Go to Withdraw section and text the Admin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Home", callback_data="home")]])
        )
        return

    if data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users[user_id]['invites'])
        text = f"Your invite link:\n{link}\n\nInvited: {count}/{MAX_INVITES}\nBalance: ${balance:.2f}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "daily":
        now = time.time()
        last = users[user_id].get("last_claimed", 0)
        if now - last >= 86400:
            users[user_id]['balance'] += 2.5
            users[user_id]['last_claimed'] = now
            text = f"You received $2.5 for daily visit.\nBalance: ${users[user_id]['balance']:.2f}"
        else:
            remaining = int(86400 - (now - last))
            h, m = divmod(remaining // 60, 60)
            text = f"You already claimed your daily reward.\nTry again in {h}h {m}m."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "admin":
        await query.edit_message_text("Chat with Admin: @Your_bot6t9", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "withdraw":
        await query.edit_message_text("The withdrawal information will be published later in the group.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "how":
        await query.edit_message_text("Ask the Admin when your balance reach to 100 USD", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "notice":
        text = "Those who completed the minimum withdrawal amount will get their Money in 20th July.\nDon't forgot to top up 0.2 solona in your account as gas fees."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "task":
        task_buttons = [
            [InlineKeyboardButton("Simple Arithmetic ($2.5)", callback_data="task_simple")],
            [InlineKeyboardButton("Watch and Earn ($40)", callback_data="task_watch")],
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
        await query.edit_message_text("Choose your task:", reply_markup=InlineKeyboardMarkup(task_buttons))

    elif data == "task_watch":
        if not users[user_id].get('watch_earned'):
            users[user_id]['balance'] += 40
            users[user_id]['watch_earned'] = True
        await context.bot.send_message(chat_id=user_id, text="Click below to watch & earn $40 👇")
        await context.bot.send_message(chat_id=user_id, text="https://doctorreward.blogspot.com/2025/06/watch-video-earn-usd.html?m=1")
        await show_home(update, context)

    elif data == "task_simple":
        today = datetime.now().date()
        user = users[user_id]
        if user['last_task_day'] != today:
            user['used_questions'] = set()
            user['daily_questions_done'] = 0
            user['last_task_day'] = today

        if user['daily_questions_done'] >= 4:
            await query.edit_message_text("You have reached today's limit of 4 questions.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))
            return

        available = [q for q in simple_questions if str(q) not in user['used_questions']]
        if not available:
            await query.edit_message_text("❌ No new questions available.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))
            return

        q, a = random.choice(available)
        user['task_stage'] = "task_simple"
        user['task_answer'] = str(a)
        user['used_questions'].add(str((q, a)))
        await query.edit_message_text(f"Answer this: {q}")

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text.strip()
    user = users.get(user_id)

    if not user:
        return

    if user['task_stage'] == "set_name":
        user['name'] = msg
        user['task_stage'] = None
        await show_home(update, context)
        return

    if user['task_stage'] == "task_simple":
        if msg.replace(" ", "") == user['task_answer']:
            if user['balance'] < EARNING_LIMIT:
                user['balance'] += 2.5
                await update.message.reply_text("✅ Correct! You earned $2.5")
            else:
                await update.message.reply_text("You've reached the $200 earning limit.")
        else:
            await update.message.reply_text("❌ Incorrect.")
        user['daily_questions_done'] += 1
        user['task_stage'] = None
        user['task_answer'] = None
        await show_home(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
