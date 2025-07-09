from __future__ import annotations

import logging
import multiprocessing
import os
import time
from typing import Generator

from logging_config import set_up_logging
from statsig_interface import StatsigInterface

logger = logging.getLogger("repro")

multiprocessing.set_start_method("fork", force=True)
StatsigInterface.initialize()


def _pass_through_task() -> None:
    """Do nothing."""
    pass


def _proc_name_generator(start: int) -> Generator:
    """Generate process names in an incrementing pattern."""
    num_concurrent_workers = max(os.cpu_count() - 1, 1)
    process_name_pattern = "my_process_{suffix}"
    for suffix in range(start, start + num_concurrent_workers):
        yield process_name_pattern.format(suffix=suffix)


def run(timeout: int) -> None:
    set_up_logging()  # a new logfile for each run

    logger.info("Starting the run...")
    proc_index = 0
    while True:
        logger.info("Starting a new batch of processes")

        # Create forks
        procs = []
        for proc_name in _proc_name_generator(start=proc_index):
            p = multiprocessing.Process(
                target=_pass_through_task,
                name=proc_name,
            )
            procs.append(p)
            p.start()

            proc_index += 1

        pid = os.getpid()

        # Monitor forks for timeouts
        start = time.time()
        while (time.time() - start) <= timeout:
            alive = [p.pid for p in procs if p.is_alive()]
            if not any(alive):
                # All the processes are done, break now.
                break

            # Print logs if procs are taking longer than expected
            elapsed = round(time.time() - start, 1)
            if elapsed > 5 and elapsed % 5 == 0:
                logger.warning(
                    f"pid {pid}: Already waited for {elapsed}s, proc PIDs: {alive}"
                )
            time.sleep(0.1)  # Just to avoid hogging the CPU

        # Terminate all forks that are still alive
        timed_out_procs = [p for p in procs if p.is_alive()]
        if any(timed_out_procs):
            logger.error(
                f"pid {pid}: timeout detected, killing all processes. Timed out procs: {timed_out_procs}"
            )
            for p in procs:
                p.terminate()
                p.join()


if __name__ == "__main__":
    run(timeout=300)  # seconds
