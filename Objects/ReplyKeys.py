import datetime

from telebot import types
from Objects.DbObjects import Hotspot


menu_button = types.InlineKeyboardButton('↪️ Меню', callback_data='{"state": "menu"}')


def menu():
    buttons = [
        types.InlineKeyboardButton('📊 Статистика Wi-Fi', callback_data='{"state": "stat-hotspots"}'),
        types.InlineKeyboardButton('⚙️ Тех. поддержка', callback_data='{"state": "support"}'),
        types.InlineKeyboardButton('Выйти', callback_data='{"state": "logout"}')
    ]
    return types.InlineKeyboardMarkup(row_width=1).add(*buttons)


def confirm_logout():
    buttons = [
        types.InlineKeyboardButton('Отмена', callback_data='{"state": "menu"}'),
        types.InlineKeyboardButton('❌ Выйти', callback_data='{"state": "logout-confirmed"}')
    ]
    return types.InlineKeyboardMarkup(row_width=2).add(*buttons)


def back_to_menu():
    return types.InlineKeyboardMarkup().add(menu_button)


def pick_hotspots(hotspots: list[Hotspot]):
    buttons = []
    callback_prefix = '{"state": "stat-period", "hotspot": '

    for hs in hotspots:
        cdata = callback_prefix + str(hs.id) + "}"
        buttons.append(types.InlineKeyboardButton(hs.name, callback_data=cdata))

    if len(hotspots) > 1:
        cdata = callback_prefix + '"all"}'
        buttons.append(types.InlineKeyboardButton("Выбрать все", callback_data=cdata))

    buttons.append(menu_button)

    return types.InlineKeyboardMarkup(row_width=1).add(*buttons)
