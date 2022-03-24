from time import sleep

import telebot
import flask

import config
from Objects import bot
from Objects.Loggers import server
from preprocess import preprocess_update
# noinspection PyUnresolvedReferences
import Dialogues


app = flask.Flask(__name__)


@app.route(config.WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        server.debug(f'Received {flask.request}')
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        preprocess_update(update)
        bot.process_new_updates([update])
        return ''
    else:
        server.warning(f'Received request with no headers: {flask.request}')
        flask.abort(403)


bot.remove_webhook()

sleep(1)

bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH)
server.info(f'Webhook set: {bot.get_webhook_info()}')
