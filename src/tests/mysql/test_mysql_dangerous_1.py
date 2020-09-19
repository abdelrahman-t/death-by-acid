import logging as LOGGER
import subprocess
import time
import unittest

from base import constants, utils


class TestDangerous(unittest.TestCase):

    def setUp(self) -> None:
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'down', '--volumes', '--remove-orphans'])
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'up', '-d', 'mysql'])

        time.sleep(25.0)

        from base import mysql
        mysql.setup()

    def test(self):
        from base import mysql
        success = utils.run_function(mysql.buy_product_dangerous_1,
                                     number_times=constants.NUMBER_OPERATIONS, username='user', product_name='product')

        with mysql.create_session() as session:
            balance = session.query(mysql.UserModel).filter(mysql.UserModel.username == 'user').first().balance

        self.assertGreaterEqual(
            balance,
            0,
            'Negative balance!'
        )
        self.assertEqual(
            balance,
            constants.INITIAL_BALANCE - (success * constants.PRODUCT_PRICE),
            'Balance is incorrect'
        )
        LOGGER.warning('Number of successful transactions: %d, Remaining balance: %d', success, balance)


if __name__ == '__main__':
    unittest.main()
