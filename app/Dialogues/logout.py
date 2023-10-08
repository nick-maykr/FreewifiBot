from app.Modules import bot
from app.Modules.Loggers import ErrLog
from app.Modules.BotDatabase import User, Users
from app.Modules.ReplyKeys import confirm_logout
from app.Modules.TgCallbacks import process_callback as process_c
from app.Modules import UsersCache


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'logout')
@ErrLog
def ask(c):
    user = User(c.from_user.id)
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    txt = "<b>Выйти из бота</b>\n\nВы уверены?"
    bot.send_message(user.id, txt, reply_markup=confirm_logout(), parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'logout-confirmed')
@ErrLog
def logout(c):
    user = User(c.from_user.id)
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    del UsersCache.states[user.id]
    Users(id=user.id).delete()
    txt = "Вы вышли из бота\nДо свидания!"
    bot.send_message(user.id, txt)
