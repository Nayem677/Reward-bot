from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")

users = {}
MAX_INVITES = 4

def get_balance(user_id):
    return users.get(user_id, {}).get("balance", 0)

def get_main_buttons():
    return [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
        [InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("👫 Friends", callback_data="invite")]
    ]

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

    await show_home(update, context)

async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    text = f"💰 Balance: ${balance:.2f}"

    buttons = [
        [InlineKeyboardButton("🎁 Daily Visit Reward", callback_data="daily")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw")]
    ] + get_main_buttons()

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

    elif data == "invite" or data == "friends":
        invite_link = f"https://t.me/{context.bot.username}?start={user_id}"
        count = len(users.get(user_id, {}).get("invites", []))
        text = (
            f"👫 Invite your friends using this link:\n{invite_link}\n\n"
            f"✅ Invited: {count}/{MAX_INVITES}\n\n💰 Balance: ${balance:.2f}"
        )
        buttons = [
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="home")]
        ] + get_main_buttons()
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "daily":
        users[user_id]['balance'] += 1
        text = f"🎁 You received $1 for daily visit!\n💰 Balance: ${get_balance(user_id):.2f}"
        buttons = [
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="home")]
        ] + get_main_buttons()
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "withdraw":
        count = len(users.get(user_id, {}).get("invites", []))
        if count >= MAX_INVITES:
            text = (
                f"✅ You've unlocked withdrawal!\n\n"
                f"🔗 Join the group: [Click here](https://t.me/+nb-JllPAKkk4ODhl)\n\n"
                f"📢 Follow the instructions in the group to withdraw your balance.\n\n"
                f"💰 Balance: ${balance:.2f}"
            )
        else:
            text = (
                f"⛔ You need 4 successful invites to unlock withdrawal.\n\n"
                f"💰 Balance: ${balance:.2f}"
            )
        buttons = [
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="home")]
        ] + get_main_buttons()
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "leaderboard":
        text = "📊 Leaderboard is under development.\n\n💰 Balance: ${:.2f}".format(balance)
        buttons = [
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="home")]
        ] + get_main_buttons()
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
