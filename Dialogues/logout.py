import Cache
from Objects import bot
from Objects.Loggers import ErrLog
from Objects.DbObjects import User, Users
from Objects.ReplyKeys import confirm_logout
from Objects.TgCallbacks import process_callback as process_c


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
    del Cache.states[user.id]
    Users(id=user.id).delete()
    txt = "Вы вышли из бота\nДо свидания!"
    bot.send_message(user.id, txt)
