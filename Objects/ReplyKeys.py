import datetime as dt
import json
from typing import Literal

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from Objects.DbObjects import Hotspot


menu_button = InlineKeyboardButton('↪️ Меню', callback_data='{"state": "menu"}')


def menu():
    buttons = [
        InlineKeyboardButton('📊 Статистика Wi-Fi', callback_data='{"state": "stat-hotspots"}'),
        InlineKeyboardButton('⚙️ Тех. поддержка', callback_data='{"state": "support"}'),
        InlineKeyboardButton('Выйти', callback_data='{"state": "logout"}')
    ]
    return InlineKeyboardMarkup(row_width=1).add(*buttons)


def confirm_logout():
    buttons = [
        InlineKeyboardButton('Отмена', callback_data='{"state": "menu"}'),
        InlineKeyboardButton('❌ Выйти', callback_data='{"state": "logout-confirmed"}')
    ]
    return InlineKeyboardMarkup(row_width=2).add(*buttons)


def back_to_menu():
    return InlineKeyboardMarkup().add(menu_button)


def pick_hotspots(hotspots: list[Hotspot]):
    buttons = []
    cb_prefix = {"state": "stat-startdate"}

    for hs in hotspots:
        cdata = cb_prefix | {"hs": hs.id}
        buttons.append(InlineKeyboardButton(hs.name, callback_data=json.dumps(cdata)))

    if len(hotspots) > 1:
        cdata = cb_prefix | {"hs": "all"}
        buttons.append(InlineKeyboardButton("Выбрать все", callback_data=json.dumps(cdata)))

    buttons.append(menu_button)

    return InlineKeyboardMarkup(row_width=1).add(*buttons)


def pick_startdate(hotspot: int | Literal['all']):
    buttons = []
    cb_prefix = {"state": "stat-export", "hs": hotspot}
    names = ["Неделя", "Месяц", "Все время"]
    cb_dates = [
        dt.date.today() - dt.timedelta(days=6),
        dt.date.today() - dt.timedelta(days=29),
        dt.date.min
    ]

    for name, cb_date in zip(names, cb_dates):
        cb_data = cb_prefix | {"dt": str(cb_date)}
        buttons.append(InlineKeyboardButton(name, callback_data=json.dumps(cb_data)))

    return InlineKeyboardMarkup(row_width=3).add(*buttons).row(menu_button)
