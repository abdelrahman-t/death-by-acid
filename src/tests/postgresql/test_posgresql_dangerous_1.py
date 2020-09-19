import logging as LOGGER
import subprocess
import time
import unittest

from base import constants, utils


class TestDangerous(unittest.TestCase):

    def setUp(self) -> None:
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'down', '--volumes', '--remove-orphans'])
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'up', '-d', 'postgresql'])

        time.sleep(25.0)

        from base import postgresql
        postgresql.setup()

    def test(self):
        from base import postgresql
        success = utils.run_function(postgresql.buy_product_dangerous_1,
                                     number_times=constants.NUMBER_OPERATIONS, username='user', product_name='product')

        with postgresql.create_session() as session:
            balance = session.query(postgresql.UserModel)\
                .filter(postgresql.UserModel.username == 'user').first().balance

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
