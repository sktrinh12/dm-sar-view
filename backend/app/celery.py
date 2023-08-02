from celery import Celery
from os import getenv
from .oracle_class import OracleCxn
from .credentials import cred_dct

celery = Celery(
    __name__,
    broker=f"redis://:{getenv('REDIS_PASSWD')}@{getenv('REDIS_HOST', '127.0.0.1')}:{getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://:{getenv('REDIS_PASSWD')}@{getenv('REDIS_HOST', '127.0.0.1')}:{getenv('REDIS_PORT', '6379')}/0",
)

celery.conf.result_expires = 3600


@celery.task
def exec_proc_outer(args_data):
    sql_stmt = args_data["sql_stmt"]
    name = args_data["name"]
    compound_id = args_data["cmp"]
    sql_column = args_data["sql_column"]
    if "pg_db" in args_data:
        cxn = OracleCxn(
            getenv("PG_HOST"),
            None,
            getenv("PG_NAME"),
            getenv("PG_USER"),
            getenv("PG_PASSWORD").strip(),
            True,
        )
    else:
        cxn = OracleCxn(
            cred_dct["HOST"],
            cred_dct["PORT"],
            cred_dct["SID"],
            cred_dct["USERNAME"],
            cred_dct["PASSWORD"],
        )
        cxn.dsn()
    payload = cxn.execute_and_process(
        sql_stmt, name, compound_id, sql_column, None, False
    )
    return payload
