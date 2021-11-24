from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional

from pydantic import BaseModel, validator
from sqlalchemy import String, Column, Integer, Numeric, DateTime, MetaData, Table

metadata = MetaData()


class UserRequest(BaseModel):
    first_name: str
    last_name: str


class UserResponse(UserRequest):
    user_id: int
    wallet_id: int


class MoneyRequest(BaseModel):
    amount: str

    @validator('amount')
    def amount_positive_number(cls, v):
        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError
        except (ValueError, InvalidOperation):
            raise ValueError(f'Amount must be a positive number. Given value {v}')
        return v


class DepositRequest(MoneyRequest):
    user_id: int


class TransferRequest(MoneyRequest):
    from_user_id: int
    to_user_id: int


class Transaction(BaseModel):
    debit_transaction_id: int
    credit_transaction_id: Optional[int]


class TransactionType(str, Enum):
    credit = 'credit'
    debit = 'debit'


users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('first_name', String),
    Column('last_name', String),
)

wallets = Table(
    'wallets',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer),
    Column('balance', Numeric(asdecimal=True)),
)

transactions = Table(
    'transactions',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('wallet_id', Integer),
    Column('type', String),
    Column('amount', Numeric(asdecimal=True)),
    Column('transaction_timestamp', DateTime),
)
