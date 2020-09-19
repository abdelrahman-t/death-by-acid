import logging as LOGGER
import subprocess
import unittest

from base import constants, mongodb, utils


class TestDangerous(unittest.TestCase):

    def setUp(self) -> None:
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'down', '--volumes', '--remove-orphans'])
        subprocess.call(['/usr/bin/sudo', 'docker-compose', 'up', '-d', 'mongodb'])

        mongodb.setup()

    def test(self):
        success = utils.run_function(mongodb.buy_product_safe,
                                     number_times=constants.NUMBER_OPERATIONS, username='user', product_name='product')
        balance: int = mongodb.get_database().users.find_one({'username': 'user'})['balance']

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
