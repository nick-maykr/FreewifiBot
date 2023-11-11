from flask_apscheduler import APScheduler
import pandas as pd
import pymysql.cursors

from Modules.Bot import bot
from Modules.BotDatabase import Hotspots
from config import (
    ADMIN_USERIDS,
    DAYS_OFFLINE_FOR_ALERT,
    MAX_MESSAGE_TEXT_LENGTH,
    PROD_DB,
)

scheduler = APScheduler()


# noinspection SqlResolve
@scheduler.task('interval', id='run_healthcheck', seconds=30)
def run_healthcheck():
    active_hotspots = Hotspots(is_active=True).select()
    q = f"""
    select 
        calledstationid, 
        max(acctstarttime) as last_connection,
        datediff(current_timestamp, max(acctstarttime)) as days_offline
    from radius.radacct 
    where calledstationid in {tuple(hs.name for hs in active_hotspots)}
    group by calledstationid
    order by days_offline desc
    """
    with pymysql.connect(**PROD_DB) as c:
        df = pd.read_sql(q, c)

    df = df[df.days_offline > DAYS_OFFLINE_FOR_ALERT]

    text = "\n\n".join(df.to_dict(orient='records'))

    for userid in ADMIN_USERIDS:
        # Split text into batches
        for i in range(0, len(text), MAX_MESSAGE_TEXT_LENGTH):
            bot.send_message(userid, text[i:i + MAX_MESSAGE_TEXT_LENGTH])
