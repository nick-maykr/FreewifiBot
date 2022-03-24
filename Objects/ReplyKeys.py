import datetime

from telebot import types


def menu():
    buttons = [
        types.InlineKeyboardButton('📊 Статистика Wi-Fi', callback_data='{"state": "stats-point"}'),
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
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton('↪️ Меню', callback_data='{"state": "menu"}')
    )
