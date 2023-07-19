from datetime import datetime, timedelta
from time import sleep
from .globals import remaining_batches

duration = timedelta(hours=5)


def purge_expired_keys():
    while True:
        current_time = datetime.now()
        keys_to_remove = []
        remaining_batches_copy = remaining_batches.copy()
        for key, lst in remaining_batches_copy.items():
            if lst:
                for *_, timestamp in lst:
                    timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    if (
                        current_time - timestamp_obj > duration
                    ):  # Check if timestamp is older than 5 hours
                        keys_to_remove.append(key)
            else:
                # empty batches
                keys_to_remove.append(key)
        for key in keys_to_remove:
            print(f"{current_time} deleting batch key, {key}")
            del remaining_batches[key]
        sleep(3600)
