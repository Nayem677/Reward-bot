from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import random
import time
from datetime import datetime, timedelta, timezone

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 10
INVITE_REWARD = 2
EARNING_LIMIT = 200

simple_questions = [("3 + 5", 8), ("9 - 2", 7), ("6 + 4", 10), ("7 - 3", 4), ("2 + 2", 4)]
complex_questions = [("12 * 2 - 4", 20), ("8 + 4 * 2", 16), ("5 * 5 + 3", 28), ("18 - 6 / 3", 16), ("10 + 12 - 4", 18)]
expressions = [("2x + 3x", "5x"), ("4a + 6a", "10a"), ("x + x + x", "3x"), ("3y - y", "2y"), ("7m - 2m", "5m")]
quadratics = [("x^2 - 5x + 6 = 0", "2,3"), ("x^2 - 3x + 2 = 0", "1,2"), ("x^2 - 4x + 3 = 0", "1,3")]

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def get_main_buttons():
    return [
        [InlineKeyboardButton("Home", callback_data="home"), InlineKeyboardButton("Refresh", callback_data="refresh")],
        [InlineKeyboardButton("Invite Friends", callback_data="invite"), InlineKeyboardButton("Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("Chat with Admin", callback_data="admin"), InlineKeyboardButton("Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("Daily Task", callback_data="task"), InlineKeyboardButton("How to Withdraw", callback_data="how")],
        [InlineKeyboardButton("📢 Payment Info", callback_data="notice"), InlineKeyboardButton("⏳ Countdown Timer", callback_data="countdown")]
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
            'used_questions': set()
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
            users[user_id]['balance'] += 1
            users[user_id]['last_claimed'] = now
            text = f"You received $1 for daily visit.\nBalance: ${users[user_id]['balance']:.2f}"
        else:
            remaining = int(86400 - (now - last))
            h, m = divmod(remaining // 60, 60)
            text = f"You already claimed your daily reward.\nTry again in {h}h {m}m."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "admin":
        await query.edit_message_text("Chat with Admin: @Your_bot6t9", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "withdraw":
        await query.edit_message_text("The withdrawal information will be published later in the group.\nBalance: ${:.2f}".format(balance), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "how":
        await query.edit_message_text("Ask the Admin when your balance reach to 100 USD", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "notice":
        text = "Those who completed the minimum withdrawal amount will get their Money in 20th July.\nDon't forgot to top up 0.2 solona in your account as gas fees."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "countdown":
        bd_time = timezone(timedelta(hours=6))
        now = datetime.now(bd_time)
        target = datetime(2024, 7, 20, 0, 0, tzinfo=bd_time)
        remaining = target - now
        if remaining.total_seconds() > 0:
            h, rem = divmod(remaining.total_seconds(), 3600)
            m, _ = divmod(rem, 60)
            countdown_text = f"⏳ Time left: {int(h)} hours, {int(m)} minutes"
        else:
            countdown_text = "⏳ Countdown Complete!"
        await query.edit_message_text(countdown_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "task":
        task_buttons = [
            [InlineKeyboardButton("Simple ($2)", callback_data="task_simple"), InlineKeyboardButton("Complex ($5)", callback_data="task_complex")],
            [InlineKeyboardButton("Simplify Expr ($10)", callback_data="task_expr"), InlineKeyboardButton("Quadratic ($10)", callback_data="task_quad")],
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
        await query.edit_message_text("Choose your task:", reply_markup=InlineKeyboardMarkup(task_buttons))

    elif data.startswith("task_"):
        user = users[user_id]
        used = user['used_questions']
        question_pool = {
            "task_simple": simple_questions,
            "task_complex": complex_questions,
            "task_expr": expressions,
            "task_quad": quadratics
        }
        reward_map = {
            "task_simple": 2,
            "task_complex": 5,
            "task_expr": 10,
            "task_quad": 10
        }

        available = [q for q in question_pool[data] if str(q) not in used]
        if not available:
            await query.edit_message_text("❌ No new questions available. Try another task.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="task")]]))
            return

        q, a = random.choice(available)
        user['task_stage'] = data
        user['task_answer'] = str(a)
        user['task_reward'] = reward_map[data]
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
        await update.message.reply_text(f"✅ Name set to {msg}")
        await show_home(update, context)
        return

    if user['task_stage']:
        correct = str(user['task_answer']).replace(" ", "")
        if msg.replace(" ", "") == correct:
            if user['balance'] >= EARNING_LIMIT:
                await update.message.reply_text(
                    "You have to withdraw your amount now, Go to Withdraw section and text the Admin.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Home", callback_data="home")]])
                )
            else:
                user['balance'] += user['task_reward']
                await update.message.reply_text(f"✅ Correct! You earned ${user['task_reward']}")
        else:
            await update.message.reply_text("❌ Incorrect.")
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
