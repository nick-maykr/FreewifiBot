import os
import random

from telebot.types import Message

from app.Modules import bot
from app.Modules.BotDatabase import User, Hotspot
from app.Modules.Excel import make_xlsx
from app.Modules.Loggers import ErrLog
from app.Modules import ReplyKeys
from app.Modules.ConnectionHistory import ConnectionCache
from app.Modules.TgCallbacks import process_callback as process_c


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

    callback_hotspot = process_c(c).hs
    callback_startdate = process_c(c).dt
    hotspots = get_picked_hotspots(user, callback_hotspot)
    hotspots = [hs for hs in hotspots if hs in user.Client.Hotspots]

    loading = send_random_sticker(user)
    bot.answer_callback_query(c.id, "Пожалуйста, подождите...")

    for hs in hotspots:

        data = ConnectionCache(hs.name).read(callback_startdate)
        if data.empty:
            txt = f"{hs.name}\nЗа выбранный период нет подключений :("
            bot.send_message(user.id, txt)
            continue

        file, filename, connection_count = make_xlsx(data, hs.name)
        bot.send_document(user.id, file, visible_file_name=filename, caption=connection_count)

    bot.delete_message(user.id, loading.id)
    bot.send_message(user.id, "Готово!", reply_markup=ReplyKeys.back_to_menu())


def send_random_sticker(user) -> Message:
    filepath = "Dialogues/stickers"
    filename = random.choice(os.listdir(filepath))
    with open(os.path.join(filepath, filename), 'rb') as sticker:
        return bot.send_sticker(user.id, sticker)
