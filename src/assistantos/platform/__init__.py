"""The OS-specific actions. Step 5: the scheduled pass. Linux is not a target yet (cron line documented, not managed)."""
import sys


def scheduler():
    if sys.platform == "win32":
        from . import windows
        return windows
    if sys.platform == "darwin":
        from . import macos
        return macos
    raise NotImplementedError("scheduling on this OS: add a cron line running `uv run aos run` every 5 minutes")
