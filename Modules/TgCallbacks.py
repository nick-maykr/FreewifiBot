"""
All callback_data in Bot's buttons is json deserializeable, but
since a bad client may send arbitrary data in this field,
we must expect it.
"""

import json
from types import SimpleNamespace

from telebot.types import CallbackQuery


class CallbackNamespace(SimpleNamespace):
    """
    Return None instead of raising AttributeError
    when accessing non-existent attributes
    """
    def __getattr__(self, item):
        return None


def process_callback(callback: CallbackQuery):
    """
    Return an object with all the attributes present in
    json deserializeable callback data.
    """
    try:
        return json.loads(callback.data, object_hook=lambda d: CallbackNamespace(**d))
    except json.decoder.JSONDecodeError:
        return CallbackNamespace()
