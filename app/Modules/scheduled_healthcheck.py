import datetime

from flask_apscheduler import APScheduler
import pandas as pd
import pymysql.cursors

from Modules.Bot import bot
from Modules.BotDatabase import Hotspots
from config import (
    CPO_USERID,
    DIR_USERID,
    DAYS_OFFLINE_FOR_ALERT,
    MAX_MESSAGE_TEXT_LENGTH,
    PROD_DB,
)

scheduler = APScheduler()


# noinspection SqlResolve
def get_problematic_hotspots() -> pd.DataFrame:
    active_hotspots = Hotspots(is_active=True).select()
    q = f"""
        select 
            calledstationid as hotspot, 
            max(acctstarttime) as last_connection,
            datediff(current_timestamp, max(acctstarttime)) as days_offline
        from radius.radacct 
        where calledstationid in {tuple(hs.name for hs in active_hotspots)}
        group by calledstationid
        order by days_offline desc
        """
    with pymysql.connect(**PROD_DB) as c:
        df = pd.read_sql(q, c)

    df = df[df.days_offline >= DAYS_OFFLINE_FOR_ALERT]
    # Correct for UTC+3
    df["last_connection"] += pd.Timedelta(hours=3)
    return df


def df_to_text_batches(df: pd.DataFrame) -> list[str]:
    """
    Telegram messages have character limit
    """
    text_batches = []
    current_text_batch = f"{df.shape[0]} hotspots, {df.days_offline.sum()} days\n---\n\n"
    for row in df.itertuples(index=False):
        text = f"{row.hotspot}\n" \
               f"Last connection: {row.last_connection}\n" \
               f"{row.days_offline} days ago\n\n"

        if len(text) > MAX_MESSAGE_TEXT_LENGTH:
            text = "<Text length error>"

        if len(current_text_batch + text) >= MAX_MESSAGE_TEXT_LENGTH:
            text_batches.append(current_text_batch)
            current_text_batch = text
            continue

        current_text_batch += text

    text_batches.append(current_text_batch)
    return text_batches


@scheduler.task('cron', id='run_healthcheck', hour=7)
def run_healthcheck():
    df = get_problematic_hotspots()
    if df.empty:
        return

    userids = [DIR_USERID]
    if datetime.date.today().day % 5 == 0:
        userids.append(CPO_USERID)

    text_batches = df_to_text_batches(df)

    for userid in userids:
        for text in text_batches:
            bot.send_message(userid, text)
