from __future__ import annotations

import datetime
import logging
import os
from statsig_python_core import Statsig, StatsigOptions
from dotenv import load_dotenv

load_dotenv()

SERVER_SDK_KEY = os.getenv("STATSIG_SERVER_SDK_KEY", "")
logger = logging.getLogger(__name__)


class StatsigInterface:
    """
    Initializes SDK and ensures safe handling of fork() events by registering
    at-fork callbacks once and only once.
    """

    # Ensure that at-fork hooks are only registered once
    _at_fork_hooks_registered = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the global Statsig client and register at-fork callbacks."""
        if not cls._at_fork_hooks_registered:
            os.register_at_fork(
                before=cls.maybe_shutdown_statsig,
                after_in_parent=cls._initialize_statsig,
                after_in_child=cls._initialize_statsig,
            )
            cls._at_fork_hooks_registered = True

        cls._initialize_statsig()

    @classmethod
    def maybe_shutdown_statsig(cls) -> None:
        """Flush pending events and dispose the shared Statsig client."""
        if Statsig.has_shared_instance():

            pid = os.getpid()
            logger.debug(f"pid {pid}: Shutting down existing Statsig...")

            start = datetime.datetime.now()

            Statsig.shared().shutdown().wait()
            Statsig.remove_shared()

            elapsed = round((datetime.datetime.now() - start).total_seconds(), 4)
            if elapsed >= 5:
                pid = os.getpid()
                logger.warning(f"pid {pid}: Shutdown and removal took a while, completed in {elapsed}s")

    @classmethod
    def _initialize_statsig(cls) -> None:
        """Initialize the global Statsig client."""
        cls.maybe_shutdown_statsig()

        pid = os.getpid()
        logger.debug(f"pid {pid}: Initializing Statsig...")

        start = datetime.datetime.now()

        options = StatsigOptions()
        options.environment = os.getenv("STATSIG_ENVIRONMENT", "development")

        if not SERVER_SDK_KEY:
            options.disable_network = True
            logger.warning(
                "No Statsig server SDK key provided – running in local mode."
            )

        shared_instance = Statsig.new_shared(SERVER_SDK_KEY, options)
        shared_instance.initialize().wait()

        elapsed = round((datetime.datetime.now() - start).total_seconds(), 4)
        if elapsed >= 5:
            logger.warning(f"pid {pid}: Init took a while, completed in {elapsed}s")
