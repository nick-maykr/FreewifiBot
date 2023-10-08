from app.Modules import bot
from app.Modules.BotDatabase import User
from app.Modules.Loggers import ErrLog
from app.Modules.ReplyKeys import menu as menu_keys
from app.Modules.TgCallbacks import process_callback as process_c


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'menu')
@ErrLog
def back_to_menu(c):
    user = User(c.from_user.id)
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    menu(user)


def menu(user):
    user.state = "menu"
    bot.send_message(user.id, "<b>Меню</b>", reply_markup=menu_keys(), parse_mode='HTML')
