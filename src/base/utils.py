import logging as LOGGER
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any, Callable, List


def run_function(func: Callable, number_times: int, ** k: Any) -> int:
    futures: List[Future] = []
    count = 0

    with ThreadPoolExecutor() as pool:

        for _ in range(number_times):
            futures.append(pool.submit(func, **k))

        for future in futures:
            try:
                future.result()
                count += 1

            except Exception as e:
                LOGGER.critical(e)

    return count
