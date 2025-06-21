from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 4

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await send_main_menu(update, context)

async def send_main_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.effective_user.id
    balance = get_balance(user_id)

    text = f"💰 Your Balance: ${balance:.2f}"

    buttons = [
        [InlineKeyboardButton("👫 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("🎁 Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")]
    ]

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update_or_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "invite":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users.get(user_id, {}).get("invites", []))
        text = (
            f"👫 Invite your friends using this link:\n\n{invite_link}\n\n"
            f"✅ Invited: {count}/{MAX_INVITES}"
        )
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "daily":
        users[user_id]['balance'] += 1
        text = "🎁 You've received $1 for today's visit!"
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "withdraw":
        count = len(users.get(user_id, {}).get("invites", []))
        if count >= MAX_INVITES:
            text = (
                "✅ You've unlocked the withdrawal process!\n\n"
                "🔗 [Join this private group](https://t.me/+nb-JllPAKkk4ODhl)\n\n"
                "📢 To withdraw your amount, join the group and follow the next procedure."
            )
        else:
            text = "⛔ You need 4 successful invites to unlock withdrawal."

        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='Markdown')

    elif data == "back":
        await send_main_menu(query, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
