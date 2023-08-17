from fastapi import FastAPI, Query, Response, Body
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from math import ceil
import uuid
from datetime import datetime, timedelta
from json import loads, dumps
from .functions import (
    execute_query_background_redis_celery,
    execute_query_background_redis_thread,
)
from .redis_connection import redis_conn
from .sql import dm_table_cols, sql_stmts
from .globals import remaining_batches
import queue
import threading
from .background_task import purge_expired_keys
from .datasource_sql import get_ds_sql
from .credentials import ENV
from .credentials import cred_dct
from .oracle_class import OracleCxn
from os import getenv


app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://sar-view-test.kinnate",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

q = queue.Queue()
background_purge = threading.Thread(target=purge_expired_keys, daemon=True)
background_purge.start()


def startup_event():
    print("Server startup")
    payload = {"biochemical": {"id": 912, "app_type": "geomean_sar"}}
    sql = get_ds_sql(payload)
    sql_stmts["biochemical_geomean"] = sql["0"]["formatted_query"]
    print("----Updated biochemical geomean sql----")
    print(sql_stmts["biochemical_geomean"])


@app.on_event("startup")
async def startup():
    startup_event()


@app.get("/")
async def home():
    return JSONResponse(
        content=f'VERSION_NUMBER: {getenv("VERSION_NUMBER", 0.1)}',
        media_type="application/json",
    )


# update sql statements dict
@app.get("/v1/update_sql_ds")
async def update_sql():
    dct_names = {
        "biochemical_geomean": {"ds_alias": "biochemical", "id": 912},
    }
    for key, dct in dct_names.items():
        payload = {dct["ds_alias"]: {"id": dct["id"], "app_type": "geomean_sar"}}
        sql = get_ds_sql(payload)
        sql_query = sql["0"]["formatted_query"]
        dct_names[key]["sql_query"] = sql_query
        sql_stmts[list(dct_names.keys())[0]] = sql_query
    return dct_names


# retrieve all request ids from redis
@app.get("/v1/request_ids")
def get_request_ids():
    regex_pattern = "*_page_*"
    request_ids = redis_conn.keys(regex_pattern)
    request_ids = [rid.decode("utf-8") for rid in request_ids]
    return JSONResponse(content=dumps(request_ids), media_type="application/json")


# delete all request ids in redis
@app.get("/v1/del_request_ids")
def del_request_ids():
    deleted = []
    regex_pattern = "*_page_*"
    request_ids = redis_conn.keys(regex_pattern)
    for request_id in request_ids:
        redis_conn.delete(request_id)
        deleted.append(request_id.decode("utf-8"))
    return JSONResponse(content=dumps(deleted), media_type="application/json")


# pass dm table name and grab compound ids
@app.get("/v1/get_cmpid_from_tbl")
async def fetch_cmpid_from(
    dm_table: str = Query(default="LIST_TESTADMIN_214006"),
) -> Response:
    cmpd_ids = []
    if dm_table:
        col_query = dm_table_cols.format(dm_table)
        cxn = OracleCxn(
            cred_dct["HOST"],
            cred_dct["PORT"],
            cred_dct["SID"],
            cred_dct["USERNAME"],
            cred_dct["PASSWORD"],
        )
        column_name = cxn.execute(col_query)  # ignore member-error
        if ENV != "PROD":
            print(col_query)
        if column_name:
            column_name = column_name[0][0]
            fetch_query = f"SELECT {column_name} AS cmpd_id FROM {dm_table}"
            rtn_data = cxn.execute(fetch_query)  # ignore member-error
            for cid in rtn_data:
                cmpd_ids.append(cid[0])
    return Response(content=dumps(cmpd_ids))


# get request id from redis for pagination
@app.get("/v1/sar_view_sql_get")
async def sar_view_sql_get(request_id: str):
    results_available = redis_conn.exists(request_id)
    if not results_available:
        raise HTTPException(status_code=404, detail="No query results available")
    results = redis_conn.get(request_id)
    data = loads(results.decode()) if results is not None else None
    return JSONResponse(
        content={"request_id": request_id, "data": data}, media_type="application/json"
    )


@app.post("/v1/sar_view_sql_update_biochem")
async def sar_view_sql_update_biochem(
    request_id: str,
    updated_data: dict = Body(...),
):
    results_available = redis_conn.exists(request_id)
    if not results_available:
        raise HTTPException(
            status_code=404,
            detail=f"request ID is wrong {request_id}, couldn't update biochem data",
        )
    # print(updated_data)
    result = redis_conn.set(request_id, dumps(updated_data["updatedData"]))
    return JSONResponse(
        content={"request_id": request_id, "status": result},
        media_type="application/json",
    )


# set request ids and trigger background task
# fast_type {1: all, 0: fast, -1: slow}
@app.post("/v1/sar_view_sql_set")
async def sar_view_sql_set(
    background_tasks: BackgroundTasks,
    request_data: dict = Body(...),
    user: str = Query(default="TESTADMIN"),
    pages: int = Query(default=10),
    fast_type: int = Query(default=0, choices=[-1, 0, 1]),
    date_filter: str = Query(
        (
            f'{(datetime.now() - timedelta(days=7)).strftime("%m-%d-%Y")}'
            f'_{datetime.now().strftime("%m-%d-%Y")}'
        )
    ),
):
    compound_ids = request_data.get("compound_ids")
    print(
        f"Query type: {fast_type} {'all' if fast_type == 1 else 'slow' if fast_type == -1 else 'fast'}"
    )
    if compound_ids is not None:
        print(f"compound id count: {len(compound_ids)}")
    else:
        print("No compound ids found.")
    print(user)
    if compound_ids is None or compound_ids == "":
        raise HTTPException(status_code=400, detail="Missing compound IDs")
    start_date, end_date = date_filter.split("_")
    print(f"{start_date} - {end_date}")
    nbr_cmpds = len(compound_ids)
    request_ids = []
    request_id = f"{str(uuid.uuid4())}_page_1"
    request_ids.append(request_id)
    # print(f"first batch: { compound_ids[:pages]}")
    paged_cmpids = compound_ids[:pages]
    if fast_type == 0:
        data = execute_query_background_redis_thread(
            q,
            request_id,
            paged_cmpids,
            start_date,
            end_date,
            fast_type,
        )
    else:
        data = execute_query_background_redis_celery(
            request_id,
            paged_cmpids,
            start_date,
            end_date,
            fast_type,
        )
    if fast_type == -1:
        return JSONResponse(
            content={
                "request_ids": request_ids,
                "data": data,
            },
            media_type="application/json",
        )
    if nbr_cmpds > pages and fast_type != -1:
        remaining_batches[f"{user}_batch"] = []
        num_batches = ceil((nbr_cmpds - pages) / pages)
        for i in range(num_batches):
            start_idx = pages + i * pages
            end_idx = pages + (i + 1) * pages
            subset_compound_ids = compound_ids[start_idx:end_idx]
            # print(f"next batch running for ... {subset_compound_ids}")
            request_id = f"{str(uuid.uuid4())}_page_{i+2}"
            request_ids.append(request_id)
            if i < pages:
                background_tasks.add_task(
                    execute_query_background_redis_celery,
                    request_id,
                    subset_compound_ids,
                    start_date,
                    end_date,
                    1,
                )
            else:
                remaining_batches[f"{user}_batch"].append(
                    (
                        request_id,
                        start_date,
                        end_date,
                        subset_compound_ids,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    )
                )
    # data = loads(results.decode()) if results is not None else None
    return JSONResponse(
        content={
            "request_ids": request_ids,
            "data": data,
        },
        media_type="application/json",
    )


# trigger next batch when page % pages == 0
@app.get("/v1/next_batch")
async def next_batch(
    background_tasks: BackgroundTasks,
    user: str,
    pages: int = Query(default=10),
):
    rtn_request_id = []
    rtn_compound_ids_batch = []
    if remaining_batches:
        key = f"{user}_batch"
        batches = remaining_batches[key][:pages]
        remaining_batches[key] = remaining_batches[key][pages:]
        for b in batches:
            (request_id, start_date, end_date, compound_ids_batch, _) = b
            rtn_request_id.append(request_id)
            rtn_compound_ids_batch.append(compound_ids_batch)
            background_tasks.add_task(
                execute_query_background_redis_celery,
                request_id,
                compound_ids_batch,
                start_date,
                end_date,
                1,
            )
    else:
        if f"{user}_batch" in remaining_batches:
            print(f"{datetime.now()} deleting batch key, {user}_batch")
            del remaining_batches[f"{user}_batch"]
    return JSONResponse(
        content={
            "request_ids": rtn_request_id,
            "compound_ids_batch": rtn_compound_ids_batch,
        },
        media_type="application/json",
    )


# show remaining batches for all users
@app.get("/v1/get_remaining_batches")
async def get_batches():
    return JSONResponse(content=remaining_batches)


# cancel batches for specified user
# must have the session id and user
@app.post("/v1/cancel_batches")
async def cancel_batches(user: str):
    if f"{user}_batch" in remaining_batches:
        del remaining_batches[f"{user}_batch"]
    return JSONResponse(
        content={
            "status": f"removed batches for {user}",
            "remaining_batches": remaining_batches,
        },
        media_type="application/json",
    )


# check background purge thread
@app.get("/v1/thread_alive")
async def thread_alive():
    return JSONResponse(
        content={"is_alive": background_purge.is_alive()}, media_type="application/json"
    )
