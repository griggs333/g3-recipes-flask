from datetime import datetime, timedelta

def format_timedelta(delta: timedelta) -> str:
    """Formats a timedelta duration to %H:%M:%S format"""
    seconds = int(delta.total_seconds())

    secs_in_a_hour = 3600
    secs_in_a_min = 60

    hours, seconds = divmod(seconds, secs_in_a_hour)
    minutes, seconds = divmod(seconds, secs_in_a_min)

    if hours >= 1:
        time_fmt = f"{hours} hr {minutes} min"
    else:
        time_fmt = f"{minutes} min"

    return time_fmt