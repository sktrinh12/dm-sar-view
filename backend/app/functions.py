import threading
from .redis_connection import redis_conn
from json import dumps
from .sql import sql_columns, sql_stmts

six_hours = 21600

case_txr = {
    "biochemical_geomean": "CREATED_DATE",
    "cellular_geomean": "CREATED_DATE",
    "in_vivo_pk": "CREATED_DATE",
    "compound_batch": "REGISTERED_DATE",
}


def case_date_highlight(name, sql_stmt, case_txr, start_date, end_date):
    if name in case_txr:
        case_info = case_txr[name]
        sql_stmt = sql_stmt.replace(
            "DATE_HIGHLIGHT",
            f"""CASE WHEN {case_info} >= TO_DATE('{start_date}',
            'MM-DD-YYYY') AND {case_info} <= TO_DATE('{end_date}',
            'MM-DD-YYYY')  THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
        )
    else:
        sql_stmt = sql_stmt.replace(
            "DATE_HIGHLIGHT",
            f"""CASE WHEN experiment_date >= TO_DATE('{start_date}',
            'MM-DD-YYYY') AND experiment_date <= TO_DATE('{end_date}',
            'MM-DD-YYYY') THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
        )
    return sql_stmt


def execute_query_background_redis(
    pool, queue, query_results_lock, request_id, compound_ids, start_date, end_date
):
    threads = []

    for cmp in compound_ids:
        for name, sql in sql_stmts.items():
            sql_stmt = sql.format(sql_columns[name], cmp)
            sql_stmt = case_date_highlight(
                name, sql_stmt, case_txr, start_date, end_date
            )
            threads.append(
                threading.Thread(
                    target=pool.execute_and_process,
                    args=(sql_stmt, queue, query_results_lock, name, cmp, sql_columns),
                )
            )

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    main_payload = {}

    while not queue.empty():
        cmpd_id, payload = queue.get()
        if cmpd_id not in main_payload:
            main_payload[cmpd_id] = {}
        main_payload[cmpd_id].update(payload)

    sorted_payload = {
        cmpd_id: {
            k: main_payload[cmpd_id][k]
            for k in ["compound_id"] + list(sql_columns.keys())
            if k in main_payload[cmpd_id]
        }
        for cmpd_id in main_payload
    }

    redis_conn.set(request_id, dumps(sorted_payload))
    redis_conn.expire(request_id, six_hours)
