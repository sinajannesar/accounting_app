"""Utility for runtime configuration and low-resource mode detection."""
import os


def low_resource_mode(db=None):
    # Priority: environment variable LOW_RESOURCE=1, then DB settings table key 'low_resource_mode'
    env = os.environ.get("LOW_RESOURCE")
    if env is not None:
        return env in ("1", "true", "True")
    if db is not None:
        try:
            val = db.get_setting("low_resource_mode", "0")
            return val in ("1", "true", "True")
        except Exception:
            return False
    return False
