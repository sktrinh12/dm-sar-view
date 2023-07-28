from celery import Celery
from os import getenv
from .oracle_class import OracleCxn
from .credentials import cred_dct

celery = Celery(
    __name__,
    broker=f"redis://:{getenv('REDIS_PASSWD')}@{getenv('REDIS_HOST', '127.0.0.1')}:{getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://:{getenv('REDIS_PASSWD')}@{getenv('REDIS_HOST', '127.0.0.1')}:{getenv('REDIS_PORT', '6379')}/0",
)


@celery.task
def exec_proc_outer(args_data):
    sql_stmt = args_data["sql_stmt"]
    name = args_data["name"]
    compound_id = args_data["cmp"]
    sql_columns = args_data["sql_columns"]
    cxn = OracleCxn(
        cred_dct["HOST"],
        cred_dct["PORT"],
        cred_dct["SID"],
        cred_dct["USERNAME"],
        cred_dct["PASSWORD"],
    )
    payload = cxn.execute_and_process(sql_stmt, name, compound_id, sql_columns)
    return payload