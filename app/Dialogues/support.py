from Modules import bot
from Modules.Loggers import ErrLog
from Modules.BotDatabase import User
from Modules.ReplyKeys import back_to_menu
from Modules.TgCallbacks import process_callback as process_c


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'support')
@ErrLog
def support_info(c):
    user = User(c.from_user.id)
    txt = "По любым вопросам вы можете написать нашим специалистам в Telegram:\n" \
          "💬 https://t.me/freewifiby\n\n\n" \
          "Либо позвонить по номеру\n📞 +375 (29) 268-05-55"
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    bot.send_message(user.id, txt, reply_markup=back_to_menu(), disable_web_page_preview=True)
