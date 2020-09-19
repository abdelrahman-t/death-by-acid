import logging as LOGGER
from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, and_, create_engine
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session as __Session
from sqlalchemy.orm import scoped_session, sessionmaker

from . import constants

database_engine = create_engine(
    'mysql+pymysql://default:default@localhost:3306/default',
    pool_size=32
)

DatabaseSession: __Session = scoped_session(
    sessionmaker(bind=database_engine)
)
SQLAlchemyBase = DatabaseModel = declarative_base()


class UserModel(DatabaseModel):  # type: ignore # pylint: disable=too-few-public-methods

    __tablename__ = 'users'

    _id = Column(INTEGER, primary_key=True)
    username = Column(String(length=50), nullable=False, index=True, unique=True)
    balance = Column(Integer, nullable=False)


class ProductModel(DatabaseModel):  # type: ignore # pylint: disable=too-few-public-methods

    __tablename__ = 'products'

    _id = Column(INTEGER, primary_key=True)
    name = Column(String(length=50), nullable=False, index=True, unique=True)
    price = Column(Integer, nullable=False)


SQLAlchemyBase.metadata.create_all(database_engine)


@contextmanager
def create_session():
    s = DatabaseSession()

    try:
        yield s
        s.commit()

    except Exception as e:
        LOGGER.exception(e)

        s.rollback()
        raise

    finally:
        s.close()


def setup() -> None:
    user = UserModel(
        username='user',
        balance=constants.INITIAL_BALANCE
    )
    product = ProductModel(
        name='product',
        price=constants.PRODUCT_PRICE
    )

    with create_session() as session:
        session.add(user)
        session.add(product)


def buy_product_dangerous_1(username: str, product_name: str) -> None:
    with create_session() as session:
        user: UserModel = session.query(UserModel).filter(UserModel.username == username).first()
        product: ProductModel = session.query(ProductModel).filter(ProductModel.name == product_name).first()

        if user.balance >= product.price:
            # Does update in application.
            user.balance -= product.price
        else:
            raise ValueError('Insufficient balance')


def buy_product_dangerous_2(username: str, product_name: str) -> None:
    with create_session() as session:
        product: ProductModel = session.query(ProductModel).filter(
            ProductModel.name == product_name).first()

        user: UserModel = session.query(UserModel).filter(
            and_(UserModel.username == username, UserModel.balance >= product.price)).first()

        if user is None:
            raise ValueError('Insufficient balance')

        # Does update inside the database.
        user.balance = UserModel.balance - product.price


def buy_product_safe(username: str, product_name: str) -> None:
    with create_session() as session:
        product: ProductModel = session.query(ProductModel).filter(ProductModel.name == product_name).first()

        # SELECT FOR UPATE
        user: UserModel = session.query(UserModel).with_for_update().filter(
            and_(UserModel.username == username, UserModel.balance >= product.price)).first()

        if user is None:
            raise ValueError('Insufficient balance')

        user.balance = UserModel.balance - product.price
