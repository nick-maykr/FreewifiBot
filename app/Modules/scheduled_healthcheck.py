from flask_apscheduler import APScheduler

from Bot import bot
from BotDatabase import Hotspots
from config import ADMIN_USERIDS, PROD_DB

scheduler = APScheduler()


@scheduler.task('interval', id='run_healthcheck', seconds=30)
def run_healthcheck():
    active_hotspots = Hotspots(is_active=True).select()
    for userid in ADMIN_USERIDS:
        bot.send_message(userid, ", ".join([hs.name for hs in active_hotspots]))
