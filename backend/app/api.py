from fastapi import FastAPI, Query, Response
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import threading
from math import ceil
import uuid
from datetime import datetime, timedelta
from .oracle_class import OraclePoolCxn
from .credentials import cred_dct
from json import loads, dumps
from .functions import execute_query_background_redis
from .redis_connection import redis_conn
from .sql import dm_table_cols


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
    json_data = dumps(request_ids)
    return JSONResponse(content=json_data, media_type="application/json")


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
        pool, request_id, compound_ids_list[:10], start_date, end_date
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
                pool,
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
