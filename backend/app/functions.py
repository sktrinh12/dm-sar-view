from .redis_connection import redis_conn
from json import dumps
from .sql import sql_columns, sql_stmts
from .celery import exec_proc_outer
from celery import group
from .worker_count import workers
from .credentials import cred_dct
import concurrent.futures
from .oracle_class import OracleCxn

expiry_time = 3600

fast_sqls = [
    "mol_structure",
    "cellular_geomean",
    "permeability",
    "protein_binding",
    "stability",
    "solubility",
    "metabolic_stability",
    "pxr",
    "in_vivo_pk",
    "compound_batch",
]

slow_sqls = [
    "biochemical_geomean",
]

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
            f"""CASE WHEN TRUNC({case_info}) >= TO_DATE('{start_date}',
            'MM-DD-YYYY') AND TRUNC({case_info}) <= TO_DATE('{end_date}',
            'MM-DD-YYYY')  THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
        )
    else:
        sql_stmt = sql_stmt.replace(
            "DATE_HIGHLIGHT",
            f"""CASE WHEN TRUNC(experiment_date) >= TO_DATE('{start_date}',
            'MM-DD-YYYY') AND TRUNC(experiment_date) <= TO_DATE('{end_date}',
            'MM-DD-YYYY') THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
        )
    return sql_stmt


def execute_query_background_redis_celery(
    request_id,
    compound_ids,
    start_date,
    end_date,
    fast_type,
):
    if fast_type == 0:
        negation = slow_sqls.copy()
    elif fast_type == -1:
        negation = fast_sqls.copy()
    else:
        negation = [-9]

    group_tasks = []
    for cmp in compound_ids:
        sub_tasks = []
        for name, sql in sql_stmts.items():
            if name in negation:
                continue
            sql_colm = sql_columns[name]
            if name == "biochemical_geomean":
                column_names = sql_colm.split(", ")
                columns_to_remove = [
                    "COMPOUND_ID",
                    "CRO",
                    "CREATED_DATE",
                ]
                filtered_column_names = [
                    column for column in column_names if column not in columns_to_remove
                ]
                sql_colm = ", ".join(filtered_column_names)
            sql_stmt = sql.format(sql_colm, cmp)
            sql_stmt = case_date_highlight(
                name, sql_stmt, case_txr, start_date, end_date
            )
            # print(sql_stmt)
            args_data = {
                "sql_stmt": sql_stmt,
                "name": name,
                "cmp": cmp,
                "sql_column": sql_colm,
            }
            sub_tasks.append(exec_proc_outer.s(args_data))
        group_tasks.append(group(sub_tasks))

    results = [group_task.apply_async() for group_task in group_tasks]
    main_payload = {}
    for result in results:
        group_result = result.get()
        for sub_result in group_result:
            compound_id, payload = sub_result
            if compound_id not in main_payload:
                main_payload[compound_id] = {}
            for key, value in payload.items():
                main_payload[compound_id][key] = value

    sorted_payload = {}
    for n, cmpd_id in enumerate(main_payload, 1):
        payload = {"row": [{"row": n}]}
        for key in ["compound_id"] + list(sql_columns.keys()):
            payload[key] = main_payload[cmpd_id].get(key, [])
        sorted_payload[cmpd_id] = payload

    if fast_type != -1:
        redis_conn.set(request_id, dumps(sorted_payload))
        redis_conn.expire(request_id, expiry_time)
    return sorted_payload


def execute_query_background_redis_thread(
    queue,
    request_id,
    compound_ids,
    start_date,
    end_date,
    fast_type,
):
    if fast_type == 0:
        negation = slow_sqls.copy()
    elif fast_type == -1:
        negation = fast_sqls.copy()
    else:
        negation = [-9]

    # print(compound_ids)

    futures = []
    orcl = OracleCxn(
        cred_dct["HOST"],
        cred_dct["PORT"],
        cred_dct["SID"],
        cred_dct["USERNAME"],
        cred_dct["PASSWORD"],
    )
    orcl.pool_connect()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for cmp in compound_ids:
            # print("-" * 50)
            for name, sql in sql_stmts.items():
                if name in negation:
                    continue
                sql_colm = sql_columns[name]
                if name == "biochemical_geomean":
                    column_names = sql_colm.split(", ")
                    columns_to_remove = ["COMPOUND_ID", "CRO", "CREATED_DATE"]
                    filtered_column_names = [
                        column
                        for column in column_names
                        if column not in columns_to_remove
                    ]
                    sql_colm = ", ".join(filtered_column_names)
                sql_stmt = sql.format(sql_colm, cmp)
                sql_stmt = case_date_highlight(
                    name, sql_stmt, case_txr, start_date, end_date
                )
                # print(sql_stmt)
                future = executor.submit(
                    orcl.execute_and_process,
                    sql_stmt,
                    name,
                    cmp,
                    sql_colm,
                    queue,
                    True,
                )
                futures.append(future)

    concurrent.futures.wait(futures)
    main_payload = {}
    orcl.pool_disconnect()

    while not queue.empty():
        cmpd_id, payload = queue.get()
        if cmpd_id not in main_payload:
            main_payload[cmpd_id] = {}
        main_payload[cmpd_id].update(payload)

    sorted_payload = {}
    for n, cmpd_id in enumerate(main_payload, 1):
        payload = {"row": [{"row": n}]}
        for key in ["compound_id"] + list(sql_columns.keys()):
            payload[key] = main_payload[cmpd_id].get(key, [])
        sorted_payload[cmpd_id] = payload

    if fast_type != -1:
        redis_conn.set(request_id, dumps(sorted_payload))
        redis_conn.expire(request_id, expiry_time)
    return sorted_payload
