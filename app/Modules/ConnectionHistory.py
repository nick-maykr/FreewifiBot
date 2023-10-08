import datetime as dt
from contextlib import closing

import numpy as np
import pandas as pd
import pymysql.cursors
import sqlite3

from app.config import CACHE_DB, WP_DB, REMOTE_DB


RADACCT_COLS = [
    'radacctid',
    'username AS mac',
    'acctstarttime',
    'acctstoptime',
    'acctsessiontime',
    'acctoutputoctets',
    'acctinputoctets',
]

WP_COLS = [
    'id',
    'time AS acctstarttime',
    'login AS mac',
    'phone'
]

CONNECTIONS_COLS = [
    'radacctid',
    'mac',
    'phone',
    'acctstarttime',
    'acctstoptime',
    'acctsessiontime',
    'acctoutputoctets',
    'acctinputoctets'
]


class ConnectionCache:

    def __init__(self, hotspot_name: str):
        self.table = hotspot_name

    def read(self, startdate=dt.date.min) -> pd.DataFrame:
        self.update()
        condition = f"'{startdate}' < acctstarttime"
        sql = f"SELECT * FROM {self.table!r} WHERE {condition}"
        with closing(sqlite3.connect(**CACHE_DB)) as c:
            return pd.read_sql(sql, c, parse_dates=['acctstarttime', 'acctstoptime'])

    def update(self):
        radacct = self._select_new_radacct_rows()

        if radacct.empty:
            reserve = 20  # in case new connections occured
            self.last_row = self._get_latest_radacctid() - reserve
            return

        new_connections = self._merge_with_wp(radacct)
        self._del_temp_connections()
        self._save_new_connections(new_connections)
        self._update_cache_info(new_connections)

    def _select_new_radacct_rows(self) -> pd.DataFrame:
        columns = ", ".join(RADACCT_COLS)
        conditions = [
            f"radacctid > {self.last_row}",
            f"calledstationid = {repr(self.table)}"
        ]
        conditions = " AND ".join(conditions)
        table = "radius.radacct"
        sql = f"SELECT {columns} FROM {table} WHERE {conditions}"
        with pymysql.connect(**REMOTE_DB) as c:
            return pd.read_sql(sql, c)

    @staticmethod
    def _merge_with_wp(radacct: pd.DataFrame) -> pd.DataFrame:
        """
        Retrieve the phone number used to authenticate each MAC
        by performing a "backward" search on connection time
        in wp_proxy_entries table.
        """
        wp = WpProxyEntries.read()
        radacct.sort_values(by='acctstarttime', inplace=True)
        wp.sort_values(by='acctstarttime', inplace=True)
        connections = pd.merge_asof(radacct, wp, on='acctstarttime', by='mac')
        connections = connections[CONNECTIONS_COLS]
        return connections

    def _del_temp_connections(self):
        """
        The connections within the last 24 hours may be unfinished,
        so they are cached temporarily and replaced with next update() call.
        """
        if not self.last_row:
            return
        sql = f"DELETE FROM {self.table!r} WHERE radacctid > {self.last_row}"
        with closing(sqlite3.connect(**CACHE_DB)) as c:
            c.execute(sql)

    def _save_new_connections(self, new_connections: pd.DataFrame):
        with closing(sqlite3.connect(**CACHE_DB)) as c:
            dtype = {'radacctid': 'INTEGER PRIMARY KEY'}
            new_connections.to_sql(
                self.table, c, if_exists="append", index=False, dtype=dtype
            )

    def _update_cache_info(self, new_conn: pd.DataFrame):
        temp_cache = new_conn.acctstarttime > dt.datetime.now() - dt.timedelta(days=1)
        last_row = new_conn[~temp_cache].radacctid.max()  # -> np.int64 | np.nan
        if not np.isnan(last_row):
            self.last_row = int(last_row)

    @staticmethod
    def _get_latest_radacctid() -> int:
        sql = f"SELECT MAX(radacctid) FROM radius.radacct"
        with pymysql.connect(**REMOTE_DB) as c:
            with c.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchone()[0]

    @property
    def last_row(self) -> int:
        sql = f"SELECT last_row FROM cache_info WHERE hotspot = {self.table!r}"
        with closing(sqlite3.connect(**CACHE_DB)) as c:
            result = c.execute(sql).fetchone()
            return result[0] if result else 0

    @last_row.setter
    def last_row(self, value):
        upd = f"UPDATE cache_info SET last_row = ? WHERE hotspot = {self.table!r}"
        ins = f"INSERT INTO cache_info VALUES ({self.table!r}, ?)"
        with closing(sqlite3.connect(**CACHE_DB)) as c:
            if not c.execute(upd, [value]).rowcount:
                c.execute(ins, [value])


class WpProxyEntries:

    @classmethod
    def read(cls):
        cls.update()
        sql = f"SELECT MAC, acctstarttime, phone FROM proxy_entries"
        with closing(sqlite3.connect(**WP_DB)) as c:
            return pd.read_sql(sql, c, parse_dates='acctstarttime')

    @classmethod
    def update(cls):
        wp = cls._select_new_wp_rows()
        if wp.empty:
            return
        with closing(sqlite3.connect(**WP_DB)) as c:
            dtype = {'id': 'INTEGER PRIMARY KEY'}
            table = "proxy_entries"
            wp.to_sql(table, c, if_exists="append", index=False, dtype=dtype)

    @classmethod
    def _select_new_wp_rows(cls) -> pd.DataFrame:
        columns = ", ".join(WP_COLS)
        table = "wifi_wp_base.wp_proxy_entries"
        sql = f"SELECT {columns} from {table} WHERE id > {cls.last_row}"
        with pymysql.connect(**REMOTE_DB) as c:
            return pd.read_sql(sql, c)

    @classmethod
    @property
    def last_row(cls) -> int:  # noqa Pycharm
        sql = f"SELECT MAX(id) FROM proxy_entries"
        with closing(sqlite3.connect(**WP_DB)) as c:
            try:
                return c.execute(sql).fetchone()[0]
            except sqlite3.OperationalError:
                return 0
