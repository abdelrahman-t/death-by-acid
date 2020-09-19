import unittest
from concurrent.futures.thread import ThreadPoolExecutor

from base.postgresql import (buy_product_dangerous_1, buy_product_dangerous_2,
                             buy_product_dangerous_3, buy_product_dangerous_4,
                             buy_product_safe)


class TestSafe(unittest.TestCase):

    def setUp(self) -> None:
        ...

    def tearDown(self):
        ...


class TestDangerous(unittest.TestCase):

    def setUp(self) -> None:
        ...

    def tearDown(self):
        ...
