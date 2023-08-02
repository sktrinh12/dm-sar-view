import cx_Oracle
from os import getenv
from .rdkit import chem_draw
from threading import Lock
import psycopg2


oracle_dir = getenv(
    "ORACLE_HOME", "/Users/spencer.trinhkinnate.com/instantclient_12_2/"
)

cx_Oracle.init_oracle_client(lib_dir=oracle_dir)


class OracleCxn:
    def __init__(self, host, port, sid, user, password, pg_db=False):
        self.host = host
        self.port = port
        self.sid = sid
        self.user = user
        self.password = password
        self._dsn = None
        self.pool = None
        self.pg_db = pg_db
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

    def dsn(self):
        self._dsn = cx_Oracle.makedsn(self.host, self.port, sid=self.sid)

    def pool_connect(self):
        self.pool = cx_Oracle.SessionPool(
            user=self.user,
            password=self.password,
            dsn=self._dsn,
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
            user=self.user, password=self.password, dsn=self._dsn, encoding="UTF-8"
        ) as connection:
            connection.outputtypehandler = self.output_type_handler
            cursor = connection.cursor()
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            return rows

    def pg_execute(self, sql_stmt):
        with psycopg2.connect(
            host=self.host, dbname=self.sid, user=self.user, password=self.password
        ) as connection:
            pg_cursor = connection.cursor()
            pg_cursor.execute(sql_stmt)
            rows = pg_cursor.fetchall()
            return rows

    def _process_rows(self, rows, name, compound_id, sql_column, queue=None):
        split_colms = sql_column.split(",")
        date_idx = len(split_colms) - 1
        with self.queue_lock:
            response = []
            payload = {}
            for row in rows:
                row_values = []
                for i, value in enumerate(row):
                    if name == "mol_structure":
                        value = chem_draw(value, 150)
                    elif name == "biochemical_geomean":
                        if i == date_idx:
                            continue
                    row_values.append(value)
                response.append(
                    dict(
                        (key.strip(), value)
                        for key, value in zip(split_colms, row_values)
                    )
                )
            # print(compound_id)
            payload[name] = response
            payload["compound_id"] = [{"FT_NUM": compound_id}]

        if queue:
            queue.put((compound_id, payload))
        return compound_id, payload

    def execute_and_process(
        self, sql_stmt, name, compound_id, sql_column, queue, pool=False
    ):
        if self.pg_db:
            rows = self.pg_execute(sql_stmt)
            return self._process_rows(rows, name, compound_id, sql_column, queue)
        else:
            if pool:
                rows = self.pool_execute(sql_stmt)
            else:
                rows = self.execute(sql_stmt)
            return self._process_rows(rows, name, compound_id, sql_column, queue)
