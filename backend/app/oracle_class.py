import cx_Oracle
from os import getenv
from .rdkit import chem_draw
from threading import Lock
from datetime import datetime
import re

oracle_dir = getenv(
    "ORACLE_HOME", "/Users/spencer.trinhkinnate.com/instantclient_12_2/"
)

cx_Oracle.init_oracle_client(lib_dir=oracle_dir)


class OracleCxn:
    def __init__(self, host, port, sid, user, password):
        self.host = host
        self.port = port
        self.sid = sid
        self.user = user
        self.password = password
        self.dsn = cx_Oracle.makedsn(self.host, self.port, sid=self.sid)
        self.pool = None
        self.queue_lock = Lock()

    def output_type_handler(self, cursor, name, default_type, size, precision, scale):
        if default_type == cx_Oracle.DB_TYPE_CLOB:
            return cursor.var(cx_Oracle.DB_TYPE_LONG, arraysize=cursor.arraysize)
        if default_type == cx_Oracle.DB_TYPE_BLOB:
            return cursor.var(cx_Oracle.DB_TYPE_LONG_RAW, arraysize=cursor.arraysize)
        if default_type == cx_Oracle.DB_TYPE_NCLOB:
            return cursor.var(
                cx_Oracle.DB_TYPE_LONG_NVARCHAR, arraysize=cursor.arraysize
            )

    def pool_connect(self):
        self.pool = cx_Oracle.SessionPool(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
            min=4,
            max=12,
            increment=1,
            threaded=True,
            encoding="UTF-8",
            max_lifetime_session=35,
        )

    def pool_disconnect(self):
        if self.pool is not None:
            self.pool.close()
            self.pool = None

    def pool_execute(
        self,
        sql_stmt,
    ):
        with self.pool.acquire() as conn:
            conn.outputtypehandler = self.output_type_handler
            cursor = conn.cursor()
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            return rows

    def execute(
        self,
        sql_stmt,
    ):
        with cx_Oracle.connect(
            user=self.user, password=self.password, dsn=self.dsn, encoding="UTF-8"
        ) as connection:
            connection.outputtypehandler = self.output_type_handler
            cursor = connection.cursor()
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            return rows

    def _process_rows(self, rows, name, sql_column):
        split_colms = sql_column.split(",")
        with self.queue_lock:
            response = []
            payload = {}
            for row in rows:
                row_values = []
                for value in row:
                    if name == "mol_structure":
                        if not re.match(r"^[A-Z]{2}\d{6}$", value):
                            value = chem_draw(value, 150)
                    elif name == "biochemical_geomean":
                        if isinstance(value, datetime):
                            continue
                    row_values.append(value)
                response.append(
                    dict(
                        (key.strip(), value)
                        for key, value in zip(split_colms, row_values)
                    )
                )
            payload[name] = response

        return payload

    def execute_and_process(self, sql_stmt, name, sql_column, pool=False):
        if pool:
            rows = self.pool_execute(sql_stmt)
        else:
            rows = self.execute(sql_stmt)
        return self._process_rows(rows, name, sql_column)
