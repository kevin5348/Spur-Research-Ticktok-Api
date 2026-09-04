from datetime import datetime, timezone


def unix_to_iso(create_time):
    if create_time is None:
        return None

    return datetime.fromtimestamp(int(create_time), tz=timezone.utc).isoformat()


def safe_str(value):
    if value is None:
        return None
    return str(value)