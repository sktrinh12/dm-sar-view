import cx_Oracle
from os import getenv
from .rdkit import chem_draw


oracle_dir = getenv(
    "ORACLE_HOME", "/Users/spencer.trinhkinnate.com/instantclient_12_2/"
)

cx_Oracle.init_oracle_client(lib_dir=oracle_dir)


class OraclePoolCxn:
    def __init__(self, host, port, sid, user, password):
        self.host = host
        self.port = port
        self.sid = sid
        self.user = user
        self.password = password
        self.pool = None

    def output_type_handler(self, cursor, name, default_type, size, precision, scale):
        if default_type == cx_Oracle.DB_TYPE_CLOB:
            return cursor.var(cx_Oracle.DB_TYPE_LONG, arraysize=cursor.arraysize)
        if default_type == cx_Oracle.DB_TYPE_BLOB:
            return cursor.var(cx_Oracle.DB_TYPE_LONG_RAW, arraysize=cursor.arraysize)
        if default_type == cx_Oracle.DB_TYPE_NCLOB:
            return cursor.var(
                cx_Oracle.DB_TYPE_LONG_NVARCHAR, arraysize=cursor.arraysize
            )

    def connect(self):
        dsn = cx_Oracle.makedsn(self.host, self.port, sid=self.sid)
        self.pool = cx_Oracle.SessionPool(
            user=self.user,
            password=self.password,
            dsn=dsn,
            min=91,
            max=150,
            increment=1,
            encoding="UTF-8",
            max_lifetime_session=35,
        )

    def disconnect(self):
        if self.pool is not None:
            self.pool.close()
            self.pool = None

    def execute(
        self,
        sql_stmt,
    ):
        with self.pool.acquire() as conn:
            conn.outputtypehandler = self.output_type_handler
            cursor = conn.cursor()
            cursor.execute(sql_stmt)
            rows = cursor.fetchall()
            return rows

    def _process_rows(
        self, rows, queue, query_results_lock, name, compound_id, sql_columns
    ):
        response = []
        payload = {}
        for row in rows:
            row_values = []
            for value in row:
                if name == "mol_structure":
                    value = chem_draw(value, 150)
                row_values.append(value)
            response.append(
                dict(
                    (key.strip(), value)
                    for key, value in zip(sql_columns[name].split(","), row_values)
                )
            )
        payload[name] = response
        payload["compound_id"] = [{"FT_NUM": compound_id}]
        with query_results_lock:
            queue.put((compound_id, payload))

    def execute_and_process(
        self, sql_stmt, queue, query_results_lock, name, compound_id, sql_columns
    ):
        rows = self.execute(sql_stmt)
        self._process_rows(
            rows, queue, query_results_lock, name, compound_id, sql_columns
        )
