from datetime import datetime, timedelta
from time import sleep
from .globals import remaining_batches

duration = timedelta(seconds=3600)


def purge_expired_keys():
    while True:
        current_time = datetime.now()
        keys_to_remove = []
        remaining_batches_copy = remaining_batches.copy()
        for key, lst in remaining_batches_copy.items():
            # print(f"{key} - {lst}")
            if lst:
                for *_, timestamp in lst[0]:
                    print(f"background purge timestamp: {timestamp}")
                    timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    if current_time - timestamp_obj > duration:
                        keys_to_remove.append(key)
            else:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            print(f"{current_time} deleting batch key, {key}")
            del remaining_batches[key]
        sleep(3600)
