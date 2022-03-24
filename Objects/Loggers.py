from telebot.types import Message

import logging
from logging.handlers import RotatingFileHandler
import os


class LevelFilter(logging.Filter):

    def __init__(self, low, high):
        self._low = low
        self._high = high
        logging.Filter.__init__(self)

    def filter(self, record):
        return self._low <= record.levelno <= self._high


class ErrLog:
    """
    Decorator class to catch errors in every function, since
    bot.process_new_updates() doesn't raise exceptions
    """

    logger = logging.getLogger('ErrLog')
    filepath = 'logs/error.log'

    def __init__(self, function):
        self.function = function
        self.add_handlers()  # stream=True for debug

    def __call__(self, *args, **kwargs):
        try:
            return self.function(*args, **kwargs)
        except Exception as e:
            msg = f'{e} in {self.function.__name__}, args={args}, kwargs={kwargs}'
            self.logger.exception(msg)

    def add_handlers(self, file=True, stream=False):
        if self.logger.handlers:
            return

        formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
        if file:
            file_handler = logging.FileHandler(self.filepath)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        if stream:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)


class MessageLogger:

    def __init__(self, user_id):
        self.user_id = user_id
        self.logger = logging.getLogger('MessageLogger')
        self.logger.setLevel(logging.INFO)
        self.handler = self.get_handler()

    def get_handler(self):
        folder = f'logs/users/{self.user_id}'
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        os.makedirs(folder, exist_ok=True)
        handler = logging.FileHandler(folder + f'/{self.user_id}.log')
        handler.setFormatter(formatter)
        return handler

    def log(self, direction, logtext, state=None):
        self.logger.addHandler(self.handler)

        if direction == 'incoming':
            self.logger.info(f'{self.user_id} ({state}): {logtext}')
        elif direction == 'outgoing':
            self.logger.info(f'BOT -> {self.user_id}: {repr(logtext)}')

        self.logger.removeHandler(self.handler)

    @staticmethod
    def get_logtext_from_message(message: Message) -> str:
        logtext = "<unknown>"
        match message.content_type:
            case 'text':
                logtext = message.text
            case 'contact':
                logtext = message.contact.phone_number
            case ('photo' | 'voice' | 'audio' | 'sticker' | 'video'
                  | 'video_note' | 'location' | 'animation'):
                logtext = f'<{message.content_type}>'
            case 'document':
                logtext = f'<document {message.document.file_name}>'
        if message.caption:
            logtext += " " + message.caption
        return logtext


class _ServerLog:

    def __init__(self):
        self.logger = logging.getLogger('Server')
        self.logger.setLevel(logging.DEBUG)
        self.add_handler()

    def add_handler(self):
        if self.logger.handlers:
            return

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
        file_handler = logging.FileHandler('logs/server.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)


class SQLLog:

    def __init__(self):
        self.logger = logging.getLogger('SQL')
        self.logger.setLevel(logging.DEBUG)
        self.add_handler()

    def add_handler(self):
        if self.logger.handlers:
            return

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
        file_handler = RotatingFileHandler('logs/sql/sql.log', maxBytes=10**7, backupCount=10)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)


sql_logger = SQLLog().logger
server = _ServerLog().logger
