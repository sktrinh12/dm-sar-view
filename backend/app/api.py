from fastapi import FastAPI, Query, Response, Body
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import threading
import queue
from math import ceil
import uuid
from datetime import datetime, timedelta
from .oracle_class import OraclePoolCxn
from .credentials import cred_dct
from json import loads, dumps
from .functions import execute_query_background_redis
from .redis_connection import redis_conn
from .sql import dm_table_cols
from os import getenv


app = FastAPI()
pool = None

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

query_results_lock = threading.Lock()
q = queue.Queue()
remaining_batches = {}


def startup_event():
    global pool
    pool = OraclePoolCxn(
        cred_dct["HOST"] if getenv("ENV", "DEV") == "PROD" else cred_dct["HOST-DEV"],
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


@app.on_event("startup")
async def startup():
    startup_event()


@app.on_event("shutdown")
async def shutdown():
    shutdown_event()


@app.get("/v1/request_ids")
def get_request_ids():
    regex_pattern = "*_page_*"
    request_ids = redis_conn.keys(regex_pattern)
    request_ids = [rid.decode("utf-8") for rid in request_ids]
    return JSONResponse(content=dumps(request_ids), media_type="application/json")


@app.get("/v1/del_request_ids")
def del_request_ids():
    deleted = []
    regex_pattern = "*_page_*"
    request_ids = redis_conn.keys(regex_pattern)
    for request_id in request_ids:
        redis_conn.delete(request_id)
        deleted.append(request_id.decode("utf-8"))
    return JSONResponse(content=dumps(deleted), media_type="application/json")


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


@app.post("/v1/sar_view_sql_hset")
async def hset_redis(
    background_tasks: BackgroundTasks,
    request_data: dict = Body(...),
    max_workers: int = Query(default=30),
    user: str = Query(default="TESTADMIN"),
    date_filter: str = Query(
        f'{(datetime.now() - timedelta(days=7)).strftime("%m-%d-%Y")}_{datetime.now().strftime("%m-%d-%Y")}'
    ),
):
    compound_ids = request_data.get("compound_ids")
    print(f"compound id count: {len(compound_ids)}")
    print(user)
    if compound_ids is None or compound_ids == "":
        raise HTTPException(status_code=400, detail="Missing compound IDs")
    start_date, end_date = date_filter.split("_")
    print(f"{start_date} - {end_date}")
    nbr_cmpds = len(compound_ids)
    request_ids = []
    request_id = f"{str(uuid.uuid4())}_page_1"
    request_ids.append(request_id)
    execute_query_background_redis(
        pool,
        q,
        query_results_lock,
        request_id,
        compound_ids[:10],
        start_date,
        end_date,
        max_workers,
    )
    results = redis_conn.get(request_id)
    if nbr_cmpds > 10:
        remaining_batches[f"{user}_batch"] = []
        num_batches = ceil((nbr_cmpds - 10) / 10)
        for i in range(num_batches):
            start_idx = 10 + i * 10
            end_idx = 10 + (i + 1) * 10
            subset_compound_ids = compound_ids[start_idx:end_idx]
            request_id = f"{str(uuid.uuid4())}_page_{i+2}"
            request_ids.append(request_id)
            if i < 10:
                background_tasks.add_task(
                    execute_query_background_redis,
                    pool,
                    q,
                    query_results_lock,
                    request_id,
                    subset_compound_ids,
                    start_date,
                    end_date,
                    max_workers,
                )
            else:
                remaining_batches[f"{user}_batch"].append(
                    (request_id, start_date, end_date, max_workers, subset_compound_ids)
                )
    data = loads(results.decode())
    return JSONResponse(
        content={
            "request_ids": request_ids,
            "data": data,
        },
        media_type="application/json",
    )


@app.get("/v1/next_batch")
async def next_batch(
    background_tasks: BackgroundTasks, user: str = Query(default="TESTADMIN")
):
    rtn_request_id = []
    rtn_compound_ids_batch = []
    if remaining_batches:
        key = f"{user}_batch"
        batches = remaining_batches[key][:10]
        remaining_batches[key] = remaining_batches[key][10:]
        for b in batches:
            (
                request_id,
                start_date,
                end_date,
                max_workers,
                compound_ids_batch,
            ) = b
            rtn_request_id.append(request_id)
            rtn_compound_ids_batch.append(compound_ids_batch)
            background_tasks.add_task(
                execute_query_background_redis,
                pool,
                q,
                query_results_lock,
                request_id,
                compound_ids_batch,
                start_date,
                end_date,
                max_workers,
            )
    return JSONResponse(
        content={
            "request_ids": rtn_request_id,
            "compound_ids_batch": rtn_compound_ids_batch,
        },
        media_type="application/json",
    )


@app.get("/v1/get_remaining_batches")
async def get_batches():
    return JSONResponse(content={"batches": remaining_batches})


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
