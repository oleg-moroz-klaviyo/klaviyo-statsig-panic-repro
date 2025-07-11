from __future__ import annotations

import datetime
import logging
import os
import time

from statsig import statsig, StatsigOptions, StatsigEnvironmentTier
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
        cls.maybe_register_at_fork_hooks()
        cls._initialize_statsig()

    @classmethod
    def maybe_register_at_fork_hooks(cls) -> None:
        """Register at-fork hooks to handle Statsig client initialization and shutdown."""
        if not cls._at_fork_hooks_registered:
            os.register_at_fork(
                before=cls.maybe_shutdown_statsig,
                after_in_parent=cls.maybe_shutdown_statsig,
                after_in_child=cls._initialize_statsig,
            )
            cls._at_fork_hooks_registered = True

    @classmethod
    def maybe_shutdown_statsig(cls) -> None:
        """Flush pending events and dispose the shared Statsig client."""
        if statsig.is_initialized():

            pid = os.getpid()
            logger.debug(f"pid {pid}: Shutting down existing Statsig...")

            start = datetime.datetime.now()

            statsig.shutdown()

            elapsed = round((datetime.datetime.now() - start).total_seconds(), 4)
            logger.debug(f"pid {pid}: Shutdown completed in {elapsed}s")
            if elapsed >= 5:
                pid = os.getpid()
                logger.warning(f"pid {pid}: Shutdown took a while, completed in {elapsed}s")

    @classmethod
    def _initialize_statsig(cls) -> None:
        """Initialize the global Statsig client."""
        cls.maybe_shutdown_statsig()

        pid = os.getpid()
        logger.debug(f"pid {pid}: Initializing Statsig...")

        start = datetime.datetime.now()

        environment = os.getenv("STATSIG_ENVIRONMENT")
        tier = (
            StatsigEnvironmentTier.production
            if environment == "production"
            else StatsigEnvironmentTier.development
        )
        options = StatsigOptions(tier=tier)

        if not SERVER_SDK_KEY:
            options.disable_network = True
            logger.warning(
                "No Statsig server SDK key provided – running in local mode."
            )

        statsig.initialize(SERVER_SDK_KEY, options)

        elapsed = round((datetime.datetime.now() - start).total_seconds(), 4)
        logger.debug(f"pid {pid}: Initialization completed in {elapsed}s")
        if elapsed >= 5:
            logger.warning(f"pid {pid}: Init took a while, completed in {elapsed}s")
