from telebot import types

from Modules.BotDatabase import PkError, User
from Modules.Loggers import MessageLogger, ErrLog
import Cache


class PreProcessor:

    def __init__(self, update: types.Update):
        self.update = update
        self.user_id = None
        self.logtext = None
        self.state = None

    def __call__(self, *args, **kwargs):
        if self.parse_update():
            self.update_cache()
            self.log_message()

    def parse_update(self) -> bool:
        if message := self.update.message:
            self.user_id = message.from_user.id
            self.logtext = MessageLogger.get_logtext_from_message(message)

        elif poll_answer := self.update.poll_answer:
            self.user_id = poll_answer.user.id
            self.logtext = f"<poll {poll_answer.poll_id}> {poll_answer.option_ids}"

        elif callback_query := self.update.callback_query:
            self.user_id = callback_query.from_user.id
            self.logtext = '<inline> ' + callback_query.data

        else:
            return False  # Unexpected type of update

        return True

    def update_cache(self):
        try:
            self.state = User(self.user_id).state
            Cache.states |= {self.user_id: self.state}
        except PkError:
            return

    def log_message(self):
        if self.logtext:
            MessageLogger(self.user_id).log('incoming', self.logtext, self.state)


@ErrLog
def preprocess_update(update):
    preprocess = PreProcessor(update)
    preprocess()
