"""TODO
- check if user has this point in db to counter malicious callback data
"""
from Objects import bot
from Objects.DbObjects import Clients, Fail2Bans, User, Users, Hotspot
from Objects.Loggers import ErrLog
from Objects import ReplyKeys
from Objects.TgCallbacks import process_callback as process_c


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'stat-hotspots')
@ErrLog
def points_ask(c):
    user = User(c.from_user.id)
    hotspots = user.Client.Hotspots
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    txt = "<b>📊 Статистика Wi-Fi</b>\n\nВыберите точку доступа:"
    bot.send_message(user.id, txt, reply_markup=ReplyKeys.pick_hotspots(hotspots), parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'stat-startdate')
@ErrLog
def startdate_ask(c):
    user = User(c.from_user.id)
    bot.answer_callback_query(c.id)
    bot.delete_message(user.id, c.message.id)
    callback_hotspot = process_c(c).hs
    hotspot_names = "\n".join(
        [hs.name for hs in get_picked_hotspots(user, callback_hotspot)]
    )
    txt = f'<b>📊 Статистика Wi-Fi</b>\n\n{hotspot_names}\n\nВыберите период:'
    bot.send_message(user.id, txt, reply_markup=ReplyKeys.pick_startdate(callback_hotspot), parse_mode="HTML")


def get_picked_hotspots(user, picked_hotspot: int | str) -> list[Hotspot]:
    if picked_hotspot == "all":
        return user.Client.Hotspots
    else:
        return [Hotspot(picked_hotspot)]


@bot.callback_query_handler(func=lambda c: process_c(c).state == 'stat-export')
@ErrLog
def export(c):
    user = User(c.from_user.id)
    bot.delete_message(user.id, c.message.id)
    bot.answer_callback_query(c.id, "Пожалуйста, подождите...")

    callback_hotspot = process_c(c).hs
    callback_startdate = process_c(c).dt
    hotspots = get_picked_hotspots(user, callback_hotspot)
    hotspots = [hs for hs in hotspots if hs in user.Client.Hotspots]

    for hs in hotspots:
        bot.send_message(user.id, hs.name)
