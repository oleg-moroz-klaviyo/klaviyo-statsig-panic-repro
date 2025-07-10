from __future__ import annotations

import psutil
import logging
import sys

logger = logging.getLogger(__name__)


class MemoryTracker:
    TERMINATE_AT_PERCENTAGE_USED = 80
    WARNING_INCREMENT = 1  # percent

    def __init__(self):
        self.initial_used_percent = None
        self.last_warned_percent = None
        self.started = False

    def start_tracking(self):
        logger.info("Starting memory tracking...")
        self.initial_used_percent = psutil.virtual_memory().percent
        self.last_warned_percent = self.initial_used_percent  # don't warn at start
        self.started = True
        logger.info(self._memory_usage())

    def check_memory_usage(self):
        if not self.started:
            self.start_tracking()

        used_percent = psutil.virtual_memory().percent
        if used_percent >= self.TERMINATE_AT_PERCENTAGE_USED:
            logger.warning(self._memory_usage())
            logger.critical(f"Available memory below {self.TERMINATE_AT_PERCENTAGE_USED}%, exiting!")
            sys.exit(1)

        increased_percent = (used_percent - used_percent % self.WARNING_INCREMENT) - self.last_warned_percent
        if increased_percent >= self.WARNING_INCREMENT:
            logger.warning(self._memory_usage())
            logger.warning(f"Memory usage has increased by {self.WARNING_INCREMENT}% or more!")
            self.last_warned_percent = used_percent - (used_percent % self.WARNING_INCREMENT)

    def _memory_usage(self):
        used_gb = self._get_used_gb()
        used_percent = psutil.virtual_memory().percent
        return f"Memory usage: {used_percent}% ({used_gb} GB)"

    def _get_used_gb(self) -> int:
        mem = psutil.virtual_memory()
        return self._bytes_to_gb(mem.total - mem.available)

    @staticmethod
    def _bytes_to_gb(num_bytes: int) -> int:
        return round(num_bytes / (1024 ** 3), 1)
