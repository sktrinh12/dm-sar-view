from datetime import datetime, timedelta
from time import sleep
from .globals import remaining_batches

duration = timedelta(hours=5)


def purge_expired_keys():
    while True:
        current_time = datetime.now()
        keys_to_remove = []
        for key, *_, timestamp in remaining_batches.items():
            timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            if (
                current_time - timestamp_obj > duration
            ):  # Check if timestamp is older than 5 hours
                keys_to_remove.append(key)
        for key in keys_to_remove:
            print(f"deleting batch key, {key}")
            del remaining_batches[key]
        sleep(3600)
