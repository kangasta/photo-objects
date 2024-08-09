try:
    from datetime import datetime, UTC
except ImportError:
    from datetime import datetime, timezone
    UTC = timezone.utc


def utcnow():
    '''Return timezone aware datetime object with current UTC time.
    '''
    return datetime.now(UTC)
