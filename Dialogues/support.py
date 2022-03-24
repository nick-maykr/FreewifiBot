import json

from Objects import bot
from Objects.Loggers import ErrLog
from Objects.DbObjects import User, Users
from Objects.ReplyKeys import confirm_logout


@bot.callback_query_handler(func=lambda c: json.loads(c.data)['state'] == 'support')
@ErrLog
def support_info(c):
    txt = ""