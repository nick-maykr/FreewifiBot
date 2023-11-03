from typing import Union, Optional
from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException

from config import BOT_TOKEN
from Modules.Loggers import MessageLogger
from Modules.Updates import preprocess_updates


class LoggerMeta(type):
    """
    Metaclass to override specific inherited methods
    to add the logging of outgoing messages.
    """

    def __new__(mcs, name, bases, dct):
        base = bases[0]
        # Inherit everything except for the overriden stuff
        for key, value in base.__dict__.items():
            dct.setdefault(key, value)

        for key, val in dct.items():
            if callable(val) and "send" in key:
                dct[key] = mcs.add_logging(val)
        return type(name, bases, dct)

    @staticmethod
    def add_logging(fn):
        def logged_fn(*args, **kwargs):
            result = fn(*args, **kwargs)
            user_id = args[1]
            logtext = args[2]
            MessageLogger(user_id).log('outgoing', logtext)
            return result
        return logged_fn


class MyBot(TeleBot, metaclass=LoggerMeta):

    def process_new_updates(self, updates):
        """
        Preprocess updates to log incoming messages,
        update UsersCache etc.
        """
        preprocess_updates(updates)
        super().process_new_updates(updates)

    # noinspection PyMethodOverriding
    def forward_message(
            self, chat_id: Union[int, str], from_chat_id: Union[int, str],
            message: types.Message, disable_notification: Optional[bool] = None,
            timeout: Optional[int] = None) -> types.Message:
        """
        Overridden to add specific logging. Signature altered deliberately.
        """
        result = super().forward_message(chat_id, from_chat_id, message.id, disable_notification, timeout)
        logtext = MessageLogger.get_logtext_from_message(message)
        MessageLogger(chat_id).log('outgoing', logtext=f"<forwarded from {from_chat_id}> {logtext}")
        return result

    def delete_message(self, chat_id: Union[int, str], message_id: int,
                       timeout: Optional[int] = None) -> bool | None:
        """
        Overridden to silence ApiTelegramExceptions.
        """
        try:
            super().delete_message(chat_id, message_id, timeout)
        except ApiTelegramException:
            return

    def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> bool | None:
        """
        Overridden to silence ApiTelegramException 429
        """
        try:
            super().unpin_all_chat_messages(chat_id)
        except ApiTelegramException as e:
            if e.error_code == 429:
                # A bug in telegtam API. Sometimes when a user has no pinned messages
                # this method will raise such an error. It is safe to ignore.
                return
            else:
                raise e


bot = MyBot(BOT_TOKEN)
