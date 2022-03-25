from Objects import bot
from Objects.DbObjects import User
from Objects.Loggers import ErrLog
from Objects.ReplyKeys import menu as menu_keys
from Objects.TgCallbacks import process_callback as process_cb


@bot.callback_query_handler(func=lambda c: process_cb(c).state == 'menu')
@ErrLog
def back_to_menu(c):
    user = User(c.from_user.id)
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    menu(user)


def menu(user):
    user.state = "menu"
    bot.send_message(user.id, "<b>Меню</b>", reply_markup=menu_keys(), parse_mode='HTML')
