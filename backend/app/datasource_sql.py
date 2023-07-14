import requests
from .backend_url import BACKEND_URL


def get_ds_sql(payload):
    url = f"http://{BACKEND_URL}/v1/fetch_ds_query"

    response = requests.get(url, json=payload)
    if response.status_code == 200:
        print(payload)
        return response.json()
    else:
        err = f"Error: {response.status_code} - {response.text}"
        print(err)
        raise
