from fastapi import FastAPI, Query, Response
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import threading
import queue
from math import ceil
import uuid

# import asyncio
from datetime import datetime, timedelta
from .sql import sql_columns, sql_stmts, dm_table_cols
from .oracle_class import OraclePoolCxn
from .credentials import cred_dct
from .redis_connection import redis_conn
from json import dumps, loads


app = FastAPI()
pool = None
twentyfour_hours = 86400

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://sar-view.kinnate",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

query_results_dict = {}
query_results_lock = threading.Lock()

case_txr = {
    "biochemical_geomean": "CREATED_DATE",
    "cellular_geomean": "CREATED_DATE",
    "in_vivo_pk": "CREATED_DATE",
    "compound_batch": "REGISTERED_DATE",
}


# def purge_expired_results():
#     current_time = datetime.now()
#     expired_keys = []

#     with query_results_lock:
#         for key, value in query_results_dict.items():
#             expiry_date = datetime.strptime(value[1], "%Y-%m-%d %H:%M:%S")
#             if expiry_date and (current_time - expiry_date) > timedelta(minutes=45):
#                 expired_keys.append(key)

#         for key in expired_keys:
#             query_results_dict.pop(key)


def execute_query_background_redis(request_id, compound_ids, start_date, end_date):
    threads = []
    q = queue.Queue()

    for cmp in compound_ids:
        for name, sql in sql_stmts.items():
            sql_stmt = sql.format(sql_columns[name], cmp)
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
            threads.append(
                threading.Thread(
                    target=pool.execute_and_process,
                    args=(sql_stmt, q, name, cmp, sql_columns),
                )
            )

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    main_payload = {}

    while not q.empty():
        cmpd_id, payload = q.get()
        if cmpd_id not in main_payload:
            main_payload[cmpd_id] = {}
        main_payload[cmpd_id].update(payload)

    sorted_payload = {
        cmpd_id: {
            k: main_payload[cmpd_id][k]
            for k in ["compound_id"] + list(sql_columns.keys())
            if k in main_payload[cmpd_id]
        }
        for cmpd_id in compound_ids
    }

    # expiry_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # expiry_payload = {"created_date": expiry_date}
    # sorted_payload.update(expiry_payload)

    redis_conn.set(request_id, dumps(sorted_payload))
    redis_conn.expire(request_id, twentyfour_hours)


# def execute_query_background(request_id, compound_ids, start_date, end_date):
#     global query_results_dict

#     threads = []
#     q = queue.Queue()

#     for cmp in compound_ids:
#         for name, sql in sql_stmts.items():
#             sql_stmt = sql.format(sql_columns[name], cmp)
#             if name in case_txr:
#                 case_info = case_txr[name]
#                 sql_stmt = sql_stmt.replace(
#                     "DATE_HIGHLIGHT",
#                     f"""CASE WHEN {case_info} >= TO_DATE('{start_date}',
#                     'MM-DD-YYYY') AND {case_info} <= TO_DATE('{end_date}',
#                     'MM-DD-YYYY')  THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
#                 )
#             else:
#                 sql_stmt = sql_stmt.replace(
#                     "DATE_HIGHLIGHT",
#                     f"""CASE WHEN experiment_date >= TO_DATE('{start_date}',
#                     'MM-DD-YYYY') AND experiment_date <= TO_DATE('{end_date}',
#                     'MM-DD-YYYY') THEN 1 ELSE 0 END DATE_HIGHLIGHT""",
#                 )
#             threads.append(
#                 threading.Thread(
#                     target=pool.execute_and_process,
#                     args=(sql_stmt, q, name, cmp, sql_columns),
#                 )
#             )

#     for t in threads:
#         t.start()
#     for t in threads:
#         t.join()

#     main_payload = {}

#     while not q.empty():
#         cmpd_id, payload = q.get()
#         if cmpd_id not in main_payload:
#             main_payload[cmpd_id] = {}
#         main_payload[cmpd_id].update(payload)

#     sorted_payload = {
#         cmpd_id: {
#             k: main_payload[cmpd_id][k]
#             for k in ["compound_id"] + list(sql_columns.keys())
#             if k in main_payload[cmpd_id]
#         }
#         for cmpd_id in compound_ids
#     }

#     with query_results_lock:
#         query_results_dict[request_id] = sorted_payload, datetime.now().strftime(
#             "%Y-%m-%d %H:%M:%S"
#         )


def startup_event():
    global pool
    pool = OraclePoolCxn(
        cred_dct["HOST"],
        cred_dct["PORT"],
        cred_dct["SID"],
        cred_dct["USERNAME"],
        cred_dct["PASSWORD"],
    )
    pool.connect()
    print("Server startup")


def shutdown_event():
    global pool
    if pool is not None:
        pool.disconnect()
    print("Server shutdown")


# async def schedule_purge():
#     while True:
#         purge_expired_results()
#         await asyncio.sleep(1800)


@app.on_event("startup")
async def startup():
    startup_event()
    # asyncio.create_task(schedule_purge())


@app.on_event("shutdown")
async def shutdown():
    shutdown_event()


@app.get("/v1/request_ids")
def get_request_ids():
    regex_pattern = "*_page_*"
    request_ids = redis_conn.keys(regex_pattern)
    json_data = dumps(request_ids)
    return JSONResponse(content=json_data, media_type="application/json")
    # return JSONResponse(content={"request_ids": list(query_results_dict.keys())})


# @app.get("/v1/sar_view_sql_get")
# async def get_request(request_id: str):
#     global query_results_dict
#     with query_results_lock:
#         results_available = request_id in query_results_dict
#     if not results_available:
#         raise HTTPException(status_code=404, detail="No query results available")
#     with query_results_lock:
#         results, expiry_date = query_results_dict.get(request_id)
#     return JSONResponse(content={"request_id": request_id, "data": results})


# @app.get("/v1/sar_view_sql_set")
# async def set_request(
#     background_tasks: BackgroundTasks,
#     compound_ids: str = Query(default="FT002787-FT007791"),
#     date_filter: str = Query(
#         f'{(datetime.now() - timedelta(days=7)).strftime("%m-%d-%Y")}_{datetime.now().strftime("%m-%d-%Y")}'
#     ),
# ):
#     if compound_ids is None or compound_ids == "":
#         raise HTTPException(status_code=400, detail="Invalid compound IDs")
#     start_date, end_date = date_filter.split("_")
#     print(f"{start_date} - {end_date}")
#     compound_ids_list = compound_ids.split("-")
#     nbr_cmpds = len(compound_ids_list)
#     request_ids = []
#     request_id = f"{str(uuid.uuid4())}_page_1"
#     request_ids.append(request_id)
#     execute_query_background(request_id, compound_ids_list[:10], start_date, end_date)
#     with query_results_lock:
#         results, expiry_date = query_results_dict.get(request_id)
#     if nbr_cmpds > 10:
#         num_batches = ceil((nbr_cmpds - 10) / 10)
#         for i in range(num_batches):
#             start_idx = 10 + i * 10
#             end_idx = 10 + (i + 1) * 10
#             subset_compound_ids = compound_ids_list[start_idx:end_idx]
#             request_id = f"{str(uuid.uuid4())}_page_{i+2}"
#             request_ids.append(request_id)
#             background_tasks.add_task(
#                 execute_query_background,
#                 request_id,
#                 subset_compound_ids,
#                 start_date,
#                 end_date,
#             )
#     return JSONResponse(
#         content={
#             "request_ids": request_ids,
#             "data": results,
#         }
#     )


@app.get("/v1/get_cmpid_from_tbl")
async def fetch_cmpid_from(
    dm_table: str = Query(default="LIST_TESTADMIN_214006"),
) -> Response:
    cmpd_ids = []
    if dm_table:
        col_query = dm_table_cols.format(dm_table)
        column_name = pool.execute(col_query)
        print(col_query)
        if column_name:
            column_name = column_name[0][0]
            fetch_query = f"SELECT {column_name} AS cmpd_id FROM {dm_table}"
            rtn_data = pool.execute(fetch_query)
            for cid in rtn_data:
                cmpd_ids.append(cid[0])
    return cmpd_ids


@app.get("/v1/sar_view_sql_hget")
async def hget_redis(request_id: str):
    results_available = redis_conn.exists(request_id)
    if not results_available:
        raise HTTPException(status_code=404, detail="No query results available")
    results = redis_conn.get(request_id)
    data = loads(results.decode())
    return JSONResponse(
        content={"request_id": request_id, "data": data}, media_type="application/json"
    )


@app.get("/v1/sar_view_sql_hset")
async def hset_redis(
    background_tasks: BackgroundTasks,
    compound_ids: str = Query(default="FT002787-FT007791"),
    date_filter: str = Query(
        f'{(datetime.now() - timedelta(days=7)).strftime("%m-%d-%Y")}_{datetime.now().strftime("%m-%d-%Y")}'
    ),
):
    if compound_ids is None or compound_ids == "":
        raise HTTPException(status_code=400, detail="Invalid compound IDs")
    start_date, end_date = date_filter.split("_")
    print(f"{start_date} - {end_date}")
    compound_ids_list = compound_ids.split("-")
    nbr_cmpds = len(compound_ids_list)
    request_ids = []
    request_id = f"{str(uuid.uuid4())}_page_1"
    request_ids.append(request_id)
    execute_query_background_redis(
        request_id, compound_ids_list[:10], start_date, end_date
    )
    results = redis_conn.get(request_id)
    if nbr_cmpds > 10:
        num_batches = ceil((nbr_cmpds - 10) / 10)
        for i in range(num_batches):
            start_idx = 10 + i * 10
            end_idx = 10 + (i + 1) * 10
            subset_compound_ids = compound_ids_list[start_idx:end_idx]
            request_id = f"{str(uuid.uuid4())}_page_{i+2}"
            request_ids.append(request_id)
            background_tasks.add_task(
                execute_query_background_redis,
                request_id,
                subset_compound_ids,
                start_date,
                end_date,
            )
    data = loads(results.decode())
    return JSONResponse(
        content={
            "request_ids": request_ids,
            "data": data,
        },
        media_type="application/json",
    )
