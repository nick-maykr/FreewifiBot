from . import start, menu, logout, support
from Objects import bot
from Objects.DbObjects import User


@bot.message_handler(content_types=['text'], func=lambda m: User(m.from_user.id).quickstate)
def delete_users_input(m):
    bot.delete_message(m.from_user.id, m.id)
