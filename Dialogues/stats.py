"""TODO
- check if user has this point in db to counter malicious callback data
"""
from Objects import bot
from Objects.DbObjects import Clients, Fail2Bans, User, Users
from Objects.Loggers import ErrLog
from Objects import ReplyKeys
from Objects.TgCallbacks import process_callback as process_cb


@bot.callback_query_handler(func=lambda c: process_cb(c).state == 'stat-hotspots')
@ErrLog
def points_ask(c):
    user = User(c.from_user.id)
    hotspots = user.Client.Hotspots
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    txt = "<b>📊 Статистика Wi-Fi</b>\n\nВыберите точку доступа:"
    bot.send_message(user.id, txt, reply_markup=ReplyKeys.pick_hotspots(hotspots), parse_mode="HTML")
