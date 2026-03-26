import pandas as pd

def to_hours(t):
    # timedelta
    if hasattr(t, "total_seconds"):
        return t.total_seconds() / 3600

    # datetime.time eða datetime
    if hasattr(t, "hour"):
        return t.hour + t.minute / 60

    # fallback
    try:
        t = pd.to_datetime(t)
        return t.hour + t.minute / 60
    except:
        return 0


def compute_shift_duration(dict_events):
    shift_dur = {}

    for j, event in dict_events.items():
        start = event["ShiftBegins"]
        end = event["ShiftEnds"]

        start_h = to_hours(start)
        end_h = to_hours(end)

        if end_h < start_h:
            end_h += 24

        dur = end_h - start_h

        # sanity check
        if dur > 10:
            print("WARNING: weird shift", j, dur)
            dur = 4

        shift_dur[j] = dur

    return shift_dur