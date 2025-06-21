from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import time

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 10
INVITE_REWARD = 3

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def get_main_buttons():
    return [
        [InlineKeyboardButton("Home", callback_data="home")],
        [InlineKeyboardButton("Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw")]
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
            'last_claimed': 0
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

    if data == "home":
        await show_home(update, context)

    elif data == "invite":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users.get(user_id, {}).get("invites", []))
        text = (
            f"Your invite link:\n{invite_link}\n\n"
            f"Invited: {count}/{MAX_INVITES}\n"
            f"Balance: ${balance:.2f}"
        )
        buttons = [
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
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

        buttons = [
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "withdraw":
        count = len(users.get(user_id, {}).get("invites", []))
        if count >= MAX_INVITES:
            text = (
                "You have unlocked withdrawal.\n\n"
                "Join the group: https://t.me/+nb-JllPAKkk4ODhl\n"
                "Follow the instructions in the group to withdraw your balance.\n\n"
                f"Balance: ${balance:.2f}"
            )
        else:
            text = (
                "Invite 10 people and get rewards.\n"
                f"You've invited {count}/10 people.\n"
                f"Balance: ${balance:.2f}"
            )

        buttons = [
            [InlineKeyboardButton("Back", callback_data="home")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
