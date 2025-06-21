from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import os

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 4

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    args = context.args

    if user_id not in users:
        users[user_id] = {'balance': 5, 'invites': set(), 'referred_by': None}

        if args:
            referrer_id = int(args[0])
            if referrer_id != user_id and referrer_id in users:
                if len(users[referrer_id]['invites']) < MAX_INVITES:
                    users[user_id]['referred_by'] = referrer_id
                    users[referrer_id]['invites'].add(user_id)
                    users[referrer_id]['balance'] += 8

    send_main_menu(update, context)

def send_main_menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    balance = get_balance(user_id)

    text = f"💰 Your Balance: ${balance:.2f}"

    buttons = [
        [InlineKeyboardButton("👫 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("🎁 Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")]
    ]

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "invite":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users.get(user_id, {}).get("invites", []))
        query.edit_message_text(
            text=f"👫 Invite your friends using this link:\n{invite_link}\n\n✅ Invited: {count}/{MAX_INVITES}"
        )

    elif data == "daily":
        users[user_id]['balance'] += 1
        query.edit_message_text("🎁 You've received $1 for today's visit!")

    elif data == "withdraw":
        count = len(users.get(user_id, {}).get("invites", []))
        if count >= MAX_INVITES:
            query.edit_message_text(
                text="✅ You've unlocked the withdrawal process!\n\n"
                     "🔗 [Join this private group](https://t.me/your_private_group)\n"
                     "📢 To withdraw your amount, join the group and follow the next procedure.",
                parse_mode='Markdown'
            )
        else:
            query.edit_message_text("⛔ You need 4 successful invites to unlock withdrawal.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
