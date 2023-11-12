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
    return df


def df_to_text_batches(df: pd.DataFrame) -> list[str]:
    text_batches = []
    current_text_batch = ""
    for row in df.itertuples(index=False):
        text = f"{row.hotspot}\n" \
               f"Last connection: {row.last_connection} " \
               f"({row.days_offline}) day(s) ago\n\n"

        if len(text) > MAX_MESSAGE_TEXT_LENGTH:
            text = "<Text length error>"

        if len(current_text_batch + text) >= MAX_MESSAGE_TEXT_LENGTH:
            text_batches.append(current_text_batch)
            current_text_batch = text
            continue

        current_text_batch += text

    text_batches.append(current_text_batch)
    return text_batches


@scheduler.task('interval', id='run_healthcheck', seconds=30)
def run_healthcheck():
    df = get_problematic_hotspots()
    if df.empty:
        return

    text_batches = df_to_text_batches(df)

    for userid in ADMIN_USERIDS:
        # Split text into batches
        for text in text_batches:
            bot.send_message(userid, text)
