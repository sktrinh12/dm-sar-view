from .redis_connection import redis_conn
from json import dumps
from .sql import sql_columns, sql_stmts
from .celery import exec_proc_outer
from celery import group

# from .worker_count import workers
# from .credentials import cred_dct
# import concurrent.futures
# from .oracle_class import OracleCxn

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


def restructure_data(original_data):
    restructured_data = {}
    tmp_data_holder = {}
    row_number = 1

    for data_object in original_data:
        for key, nested_objects in data_object.items():
            for nested_object in nested_objects:
                compound_id = nested_object["COMPOUND_ID"]
                del nested_object["COMPOUND_ID"]

                if compound_id not in tmp_data_holder:
                    tmp_data_holder[compound_id] = {
                        "row": [{"row": row_number}],
                        "compound_id": [{"FT_NUM": compound_id}],
                    }
                    row_number += 1

                if key not in tmp_data_holder[compound_id]:
                    tmp_data_holder[compound_id][key] = []

                tmp_data_holder[compound_id][key].append(nested_object)

    for compound_id in tmp_data_holder:
        restructured_data[compound_id] = {}
        for key in ["row", "compound_id"] + list(sql_columns.keys()):
            restructured_data[compound_id][key] = tmp_data_holder[compound_id].get(
                key, []
            )
    return restructured_data


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

    cmp_ids_in_clause = ", ".join(["'{}'".format(cmp) for cmp in compound_ids])
    cmp_ids_parentheses = "(" + cmp_ids_in_clause + ")"
    # print(cmp_ids_in_clause)
    sub_tasks = []
    for name, sql in sql_stmts.items():
        if name in negation:
            continue
        sql_colm = sql_columns[name]
        sql_stmt = sql.replace("'{1}'", "{1}").format(sql_colm, cmp_ids_parentheses)
        if name == "mol_structure":
            sql_stmt = sql_stmt.replace(
                "WHERE FORMATTED_ID = ", "WHERE FORMATTED_ID IN "
            )
            sql_colm = sql_colm.replace("FORMATTED_ID", "COMPOUND_ID")
        else:
            sql_stmt = sql_stmt.replace("WHERE COMPOUND_ID = ", "WHERE COMPOUND_ID IN ")
        if name == "biochemical_geomean":
            select_index = sql_stmt.find("SELECT")
            if select_index != -1:
                sql_stmt = (
                    sql_stmt[:select_index]
                    + "SELECT max(t0.compound_id) as compound_id, "
                    + sql_stmt[select_index + len("SELECT") :]
                )
            sql_stmt = sql_stmt.replace(
                "WHERE t0.compound_id = ", "WHERE t0.compound_id IN "
            )
        sql_stmt = case_date_highlight(name, sql_stmt, case_txr, start_date, end_date)
        # print(sql_stmt)
        args_data = {
            "sql_stmt": sql_stmt,
            "name": name,
            "sql_column": sql_colm,
        }
        sub_tasks.append(exec_proc_outer.s(args_data))

    results = group(*sub_tasks).apply_async().get()

    results = restructure_data(results)

    redis_conn.set(request_id, dumps(results))
    redis_conn.expire(request_id, expiry_time)
    print(f"redis set: {request_id}")
    return results
