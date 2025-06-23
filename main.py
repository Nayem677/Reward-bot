from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os
import random
import time

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 10
INVITE_REWARD = 3

simple_questions = [
    ("3 + 5", 8), ("9 - 2", 7), ("6 + 4", 10), ("7 - 3", 4), ("2 + 2", 4)
]
complex_questions = [
    ("12 * 2 - 4", 20), ("8 + 4 * 2", 16), ("5 * 5 + 3", 28), ("18 - 6 / 3", 16), ("10 + 12 - 4", 18)
]

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def get_main_buttons():
    return [
        [
            InlineKeyboardButton("Home", callback_data="home"),
            InlineKeyboardButton("Refresh", callback_data="refresh")
        ],
        [
            InlineKeyboardButton("Invite Friends", callback_data="invite"),
            InlineKeyboardButton("Daily Visit Reward", callback_data="daily")
        ],
        [
            InlineKeyboardButton("Chat with Admin", callback_data="admin"),
            InlineKeyboardButton("Withdraw", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("Daily Task", callback_data="task"),
            InlineKeyboardButton("How to Withdraw", callback_data="how")
        ]
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
            'task_answer': None
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
    text = f"Balance: ${balance:.2f}"

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

    if data == "home" or data == "refresh":
        await show_home(update, context)

    elif data == "invite":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users.get(user_id, {}).get("invites", []))
        text = (
            f"Your invite link:\n{invite_link}\n\n"
            f"Invited: {count}/{MAX_INVITES}\n"
            f"Balance: ${balance:.2f}"
        )
        buttons = [[InlineKeyboardButton("Back", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "daily":
        now = time.time()
        last = users[user_id].get("last_claimed", 0)
        if now - last >= 86400:
            users[user_id]['balance'] += 1
            users[user_id]['last_claimed'] = now
            text = f"You received $1 for daily visit.\nBalance: ${users[user_id]['balance']:.2f}"
        else:
            remaining = int(86400 - (now - last))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            text = f"You already claimed your daily reward.\nTry again in {hours}h {minutes}m.\nBalance: ${balance:.2f}"

        buttons = [[InlineKeyboardButton("Back", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "admin":
        text = "Chat with Admin: @Your_bot6t9"
        buttons = [[InlineKeyboardButton("Back", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "withdraw":
        text = "The withdrawal information will be published later in the group.\nBalance: ${:.2f}".format(balance)
        buttons = [[InlineKeyboardButton("Back", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "how":
        text = "Ask the Admin when your balance reach to 100 USD"
        buttons = [[InlineKeyboardButton("Back", callback_data="home")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "task":
        buttons = [
            [InlineKeyboardButton("Simple Task ($1)", callback_data="task_simple")],
            [InlineKeyboardButton("Complex Task ($2)", callback_data="task_complex")],
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
        await query.edit_message_text("Choose your task:", reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "task_simple":
        question, answer = random.choice(simple_questions)
        users[user_id]['task_stage'] = "simple"
        users[user_id]['task_answer'] = answer
        await query.edit_message_text(f"Answer this: {question}")

    elif data == "task_complex":
        question, answer = random.choice(complex_questions)
        users[user_id]['task_stage'] = "complex"
        users[user_id]['task_answer'] = answer
        await query.edit_message_text(f"Answer this: {question}")

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id in users and users[user_id]['task_stage']:
        try:
            if int(message) == users[user_id]['task_answer']:
                if users[user_id]['task_stage'] == "simple":
                    users[user_id]['balance'] += 1
                    await update.message.reply_text("✅ Correct! You earned $1.")
                else:
                    users[user_id]['balance'] += 2
                    await update.message.reply_text("✅ Correct! You earned $2.")
            else:
                await update.message.reply_text("❌ Incorrect answer.")

        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")

        users[user_id]['task_stage'] = None
        users[user_id]['task_answer'] = None
        await show_home(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
