import requests
from .backend_url import BACKEND_URL


def get_ds_sql():
    url = f"http://{BACKEND_URL}/v1/fetch_ds_query"
    # this needs to match dictionary.py key
    ds_name = "biochem"
    payload = {ds_name: {"id": 912, "app_type": "sar"}}

    response = requests.get(url, json=payload)
    if response.status_code == 200:
        print(f"update {ds_name} ({payload[ds_name]['id']})")
        return response.json()
    else:
        err = f"Error: {response.status_code} - {response.text}"
        print(err)
        raise
