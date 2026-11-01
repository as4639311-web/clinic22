from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC 'now' (stored columns are naive UTC); replaces deprecated utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
