from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import random
import time

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 10
INVITE_REWARD = 2
EARNING_LIMIT = 200

# ✅ NEW QUESTION SETS
simple_questions = [
    ("5 + 7", "12"), ("12 - 3", "9"), ("4 × 6", "24"), ("18 ÷ 3", "6"),
    ("9 + 8", "17"), ("14 - 5", "9"), ("7 × 5", "35"), ("20 ÷ 4", "5"),
    ("6 + 13", "19"), ("11 - 6", "5"), ("3 × 8", "24"), ("24 ÷ 6", "4"),
    ("10 + 15", "25"), ("30 - 12", "18"), ("5 × 9", "45"), ("16 ÷ 4", "4"),
    ("25 + 25", "50"), ("60 - 20", "40"), ("8 × 7", "56"), ("56 ÷ 7", "8")
]

complex_questions = [
    ("25 + 36 - 12", "49"), ("50 × 2 + 30", "130"), ("(8 + 6) × 3", "42"),
    ("144 ÷ 12 + 6", "18"), ("100 - 45 + 20", "75"), ("200 ÷ 4 - 10", "40"),
    ("(15 + 5) × 2", "40"), ("81 ÷ (9 - 6)", "27"), ("64 ÷ 8 × 2", "16"),
    ("55 + (25 - 10)", "70"), ("(45 ÷ 5) + 3", "12"), ("(100 - 60) ÷ 2", "20"),
    ("(30 × 2) + 15", "75"), ("(90 ÷ 3) - 10", "20"), ("(18 + 12) ÷ 3", "10"),
    ("(60 + 20) ÷ 4", "20"), ("(72 ÷ 8) + (12 ÷ 4)", "12"),
    ("(40 - 20) × 3", "60"), ("(96 ÷ 8) + (16 ÷ 4)", "16"),
    ("(120 - 30) ÷ (18 ÷ 3)", "15")
]

expressions = [
    ("x + 5", "x + 5"), ("x - 3", "x - 3"), ("2x - 2x", "0"), ("x ÷ 4", "x/4"),
    ("x + 7", "x + 7"), ("x - 6", "x - 6"), ("3x + 9x", "12x"), ("x ÷ 5", "x/5"),
    ("x + 9", "x + 9"), ("x - 2", "x - 2"), ("5x - 5x", "0"), ("x ÷ 2", "x/2"),
    ("x + 12", "x + 12"), ("x - 8", "x - 8"), ("4x + 3x", "7x"),
    ("x ÷ 3", "x/3"), ("x + 6", "x + 6"), ("x - 4", "x - 4"),
    ("6x - x", "5x"), ("x ÷ 6", "x/6")
]

quadratics = [
    ("2x + 5 - 3x", "-x + 5"), ("3(x + 4)", "3x + 12"), ("4x - 2 + 6x", "10x - 2"),
    ("5(x - 3) + 2x", "7x - 15"), ("(2x + 3) - (x - 4)", "x + 7"),
    ("3(x + 2) - x", "2x + 6"), ("(4x - 1) + (2x + 5)", "6x + 4"),
    ("2(x - 3) + 3(x + 1)", "5x - 3"), ("6x - (2x + 4)", "4x - 4"),
    ("(3x + 5) - (x + 2)", "2x + 3"), ("7x - 4x + 9", "3x + 9"),
    ("2(x + 3) + 3(x - 2)", "5x + 0"), ("5(x - 1) - x", "4x - 5"),
    ("4x - 3x + 7", "x + 7"), ("(2x + 6) + (x - 4)", "3x + 2"),
    ("3x + 2 - 5x + 7", "-2x + 9"), ("(6x - 3) - (2x + 1)", "4x - 4"),
    ("x + x + x + 2x", "5x"), ("(2x - 5) + (3x + 4)", "5x - 1"),
    ("8x - (2x - 6)", "6x + 6")
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
        await query.edit_message_text("The withdrawal information will be published later in the group.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "how":
        await query.edit_message_text("Ask the Admin when your balance reach to 100 USD", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

    elif data == "notice":
        text = "Those who completed the minimum withdrawal amount will get their Money in 20th July.\nDon't forgot to top up 0.2 solona in your account as gas fees."
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="home")]]))

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
        pool_map = {
            "task_simple": simple_questions,
            "task_complex": complex_questions,
            "task_expr": expressions,
            "task_quad": quadratics
        }
        reward_map = {
            "task_simple": 2, "task_complex": 5,
            "task_expr": 10, "task_quad": 10
        }

        available = [q for q in pool_map[data] if str(q) not in used]
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
