from datetime import datetime, timedelta
from time import sleep
from .globals import remaining_batches

seconds = 3600
duration = timedelta(seconds=seconds)


def purge_expired_keys():
    while True:
        current_time = datetime.now()
        keys_to_remove = []
        remaining_batches_copy = remaining_batches.copy()
        for key, lst in remaining_batches_copy.items():
            # print(f"{key} - {lst}")
            try:
                if lst:
                    for item in lst:
                        _, _, _, _, timestamp = item
                        # print(f"background purge timestamp: {timestamp}")
                        timestamp_obj = datetime.strptime(
                            timestamp, "%Y-%m-%d %H:%M:%S"
                        )
                        if current_time - timestamp_obj > duration:
                            keys_to_remove.append(key)
                            break
                else:
                    keys_to_remove.append(key)
            except Exception as e:
                print(f"ERROR purging remaining_batches [{lst}]: {e}")
        for key in keys_to_remove:
            print(f"{current_time} deleting batch key, {key}")
            del remaining_batches[key]
        sleep(seconds)
