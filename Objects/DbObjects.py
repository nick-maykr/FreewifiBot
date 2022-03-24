from __future__ import annotations

import datetime
import sqlite3

import Cache
from Objects.Loggers import sql_logger


class PkError(Exception):
    """ Number of rows with such primary key != 1 """
    pass


class UpdateError(Exception):
    """ No rows were updated """
    pass


class Query:

    def __init__(self, sql, item=None, params=None):
        self.sql = sql
        self.item = item
        self.params = params or list()
        self.rows, self.rowcount = self.execute()

    def execute(self):
        conn = sqlite3.connect('databases/clients.db', isolation_level=None)
        conn.execute("PRAGMA foreign_keys = 1")
        sql_logger.debug(self.sql)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(self.sql, self.params)
            rows = cursor.fetchall()
            return rows, cursor.rowcount
        finally:
            conn.close()


class _Row:
    """
    Row instance can be created ether by primary key - User(123) -
    or by sqlite3.Row object - User(row=row).

    When created by sqlite3.Row, all the attributes present in sqlite3.Row
    are set (added to __dict__) in the Row instance.
    Later these attributes of such instance can't be retreived from DB.

    Creation with compound primary key from **kwargs not implemented.
    """

    pk_name = "id"  # default primary key name
    table = None

    def __init__(self,
                 primary_key_value: int | str | None = None,
                 row: sqlite3.Row | None = None
                 ):
        if primary_key_value:
            self.__set(self.pk_name, primary_key_value)  # alias attribute
            self.__set("pk", primary_key_value)
        elif row:
            row_dict = dict(zip(row.keys(), tuple(row)))
            self.__set("pk", row_dict[self.pk_name])
            for key, value in row_dict.items():
                self.__set(key, value)

    def __getattr__(self, item) -> int | str | None:
        SQL = f"SELECT {item} FROM {self.table} WHERE {self.pk_name} = {repr(self.pk)}"
        rows = Query(SQL, item=item).rows
        if not rows:
            raise PkError(f"{self.pk_name} doesn't exist")
        if len(rows) > 1:
            raise PkError(f"{self.pk_name} isn't unique")
        return rows[0][item]

    def __setattr__(self, key: str, value):

        if hasattr(type(self), key):
            """ 
            Allow @property.setters and setting class variables to work.
            This doesn't affect those instance attributes, which are set
            by initializing from sqlite3.Row object 
            """
            return self.__set(key, value)

        if value is None:
            SQL = f"UPDATE {self.table} SET {key} = null WHERE {self.pk_name} = {repr(self.pk)}"
        else:
            SQL = f"UPDATE {self.table} SET {key} =:value WHERE {self.pk_name} = {repr(self.pk)}"

        Query(SQL, params={"value": value})

    def __set(self, name: str, value):
        """ Alias for superclass __setattr__ """
        return super(_Row, self).__setattr__(name, value)

    def __eq__(self, other):
        return (self.table == other.table) & (self.pk == other.pk)


class _ImmutableRow:
    """ Detached from db immutable dataclass-like objects
    to be created from sqlite3.Row objects
    """

    def __init__(self, row: sqlite3.Row):
        row_dict = dict(zip(row.keys(), tuple(row)))
        for key, value in row_dict.items():
            super().__setattr__(key, value)

    def __getattr__(self, item):
        raise AttributeError

    def __setattr__(self, key, value):
        raise NotImplementedError

    def __delattr__(self, item):
        raise NotImplementedError


class _Table:
    """ Base class for database tables.
     Tables are used to get _Row objects with flexible queries """

    table = None
    RowObject = _ImmutableRow
    items = ["id"]
    condition = "1"

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._construct_sql_condition()

    def _construct_sql_condition(self):
        for key, value in self.kwargs.items():
            match value:
                case list() if len(value) > 1:
                    cond = f"{key} IN {*value,}"
                case list() if len(value) == 1:
                    cond = f"{key} = {repr(value[0])}"
                case int() | str():
                    cond = f"{key} = {repr(value)}"
                case None:
                    cond = f"{key} is NULL"
                case _:
                    continue
            self.condition += f" AND {cond}"

    def select(self):
        sql = f"SELECT DISTINCT {', '.join(self.items)} FROM {self.table} WHERE {self.condition}"
        return [self.RowObject(row=row) for row in Query(sql).rows]

    def insert(self, ignore_integrity=True, return_row=False):
        """ Supports only one row inserts """

        keys = ', '.join(self.kwargs.keys())
        values = list(self.kwargs.values())
        placeholder = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO {self.table} ({keys}) VALUES ({placeholder})"
        try:
            Query(sql, params=values)
        except sqlite3.IntegrityError as e:
            if ignore_integrity:
                pass
            else:
                raise e
        if return_row:  # to get the auto-incremented value
            return self.select()[0]

    def delete(self):
        sql = f"DELETE FROM {self.table} WHERE {self.condition}"
        Query(sql)


class Client(_Row):
    """ id | password | name """
    table = "clients"


class Clients(_Table):
    """ id | password | name """
    table = "clients"
    RowObject = Client


class Fail2Ban(_Row):
    """ id | failed_attempts """
    table = "fail2ban"
    threshold = 3

    @property
    def remaining(self) -> int:
        return self.threshold - (self.failed_attempts or 0)


class Fail2Bans(_Table):
    """ id | failed_attempts """
    table = "fail2ban"


class User(_Row):
    """ id | client | tg_name | state """
    table = "users"

    @property
    def quickstate(self) -> str:
        return Cache.states.get(self.id)

    @property
    def Client(self) -> Client:
        return Client(self.id)

    @property
    def Fail2Ban(self) -> Fail2Ban:
        return Fail2Ban(self.id)


class Users(_Table):
    """ id | client | tg_name | state """
    table = "users"
    RowObject = User
