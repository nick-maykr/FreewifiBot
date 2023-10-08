from . import start, menu, logout, support, stats
from app.Modules import bot
from app.Modules.BotDatabase import User


@bot.message_handler(commands=['start'], func=lambda m: User(m.from_user.id).client)
def restart(m):
    user = User(m.from_user.id)
    menu.menu(user)


@bot.message_handler(content_types=['text'], func=lambda m: User(m.from_user.id).quickstate)
def delete_users_input(m):
    """
    Works for authorized or banned users.
    """
    bot.delete_message(m.from_user.id, m.id)
