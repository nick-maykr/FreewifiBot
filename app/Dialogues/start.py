from bcrypt import checkpw
from telebot.types import Message

from Modules import bot
from Modules.BotDatabase import Clients, Fail2Bans, User, Users
from Modules.Loggers import ErrLog
from Dialogues import menu


@bot.message_handler(commands=['start'],
                     func=lambda m: not User(m.from_user.id).quickstate)
@ErrLog
def start(m):
    user = User(m.from_user.id)
    insert_into_db(user, m)
    try:
        payload = m.text.split(" ")[1]
        authenticate(user, payload)
    except IndexError:
        info(user)


def insert_into_db(user, m: Message):
    first_name = m.from_user.first_name
    last_name = m.from_user.last_name
    tg_name = f"{first_name} {last_name}" if last_name else first_name
    Users(id=user.id, tg_name=tg_name).insert()
    Fail2Bans(id=user.id).insert()


def info(user):
    txt = "👋 Привет!\n" \
          "Этот бот только для клиентов Freewifi.\n" \
          "Попросите ссылку для авторизации у своего менеджера :)"
    bot.send_message(user.id, txt)


def authenticate(user, payload: str):
    try:
        client_id, password = payload.split("_", maxsplit=1)
        client = Clients(id=client_id).select()[0]
        if checkpw(bytes(password, "utf-8"), bytes(client.password, "utf-8")):
            user.client = client.id
            login(user)
        else:
            raise ValueError
    except (IndexError, ValueError):
        deny(user)


def deny(user):
    """
    To unban a user his state must be manually reset in the users tabe.
    Resetting fail2ban.failed_attempts is optional.
    """

    user.Fail2Ban.failed_attempts += 1
    remaining = user.Fail2Ban.remaining
    if remaining > 0:  # this value can get negative if DB is manipulated wrongly
        txt = f"⚠️ Неверная ссылка авторизации. Осталось попыток: {remaining}"
    else:
        user.state = "banned"
        txt = "❌ Доступ заблокирован.\nОбратитесь к своему менеджеру"
    bot.send_message(user.id, txt)


def login(user):
    bot.send_message(user.id, "Добро пожаловать!")
    menu.menu(user)
