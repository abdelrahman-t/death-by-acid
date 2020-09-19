import pymongo
from pymongo import MongoClient

from . import constants


def get_database() -> MongoClient:
    client = MongoClient(username='default', password='default', w=1)
    client.default.users.create_index(
        [
            ('username', pymongo.DESCENDING)
        ],
        unique=True
    )
    client.default.products.create_index(
        [
            ('name', pymongo.DESCENDING)
        ],
        unique=True
    )
    return client.default


def setup() -> None:
    get_database().users.insert_one(
        {
            'username': 'user',
            'balance': constants.INITIAL_BALANCE
        }
    )
    get_database().products.insert_one(
        {
            'name': 'product',
            'price': constants.PRODUCT_PRICE
        }
    )


def buy_product_dangerous_1(username: str, product_name: str) -> None:
    database = get_database()

    # Get user and product
    user = database.users.find_one({'username': username})
    product = database.products.find_one({'name': product_name})

    if user['balance'] >= product['price']:
        result = database.users.update_one(
            {
                'username': username
            },
            {
                '$set': {'balance': user['balance'] - product['price']}
            }
        )
        if result.modified_count != 1 or not result.acknowledged:
            raise ValueError('Update failed!')

    else:
        raise ValueError('Insufficient balance!')


def buy_product_dangerous_2(username: str, product_name: str) -> None:
    database = get_database()

    # Get user and product
    user = database.users.find_one({'username': username})
    product = database.products.find_one({'name': product_name})

    if user['balance'] >= product['price']:
        result = database.users.update_one(
            {
                'username': username
            },
            {
                '$inc': {'balance': -product['price']}
            }
        )
        if result.modified_count != 1 or not result.acknowledged:
            raise ValueError('Update failed!')

    else:
        raise ValueError('Insufficient balance!')


def buy_product_safe(username: str, product_name: str) -> None:
    database = get_database()

    product = database.products.find_one({'name': product_name})
    result = database.users.update_one(
        {
            'username': username,
            'balance': {'$gte': product['price']}
        },
        {
            '$inc': {'balance': -product['price']}
        }
    )
    if result.modified_count != 1 or not result.acknowledged:
        raise ValueError('Update failed!')
