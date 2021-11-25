from decimal import Decimal
from typing import Dict

from sqlalchemy import select, and_

from src.main.model import Transaction, wallets, transactions, TransactionType, UserRequest, users, UserResponse
from src.main.settings import database
from src.main.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


@database.transaction()
async def create_user(request: UserRequest) -> UserResponse:
    """Inserts user and corresponding wallet"""
    query = users.insert().values(**request.dict())
    user_id = await database.execute(query)
    query = wallets.insert().values(user_id=user_id)
    wallet_id = await database.execute(query)
    return UserResponse(**request.dict(), user_id=user_id, wallet_id=wallet_id)


@database.transaction()
async def insert_transaction(wallet_id: int, type: TransactionType, amount: Decimal) -> int:
    query = transactions.insert().values(wallet_id=wallet_id, type=type, amount=amount)
    return await database.execute(query)


@database.transaction()
async def update_balance(user_id: int, amount: Decimal) -> Decimal:
    query = (wallets.update()
             .where(wallets.c.user_id == user_id)
             .values(balance=wallets.c.balance + amount)
             .returning(wallets.c.balance))
    return await database.execute(query)


async def get_user(first_name: str, last_name: str) -> Dict:
    query = users.select().where(and_(users.c.first_name == first_name,
                                      users.c.last_name == last_name))
    user_row = await database.fetch_one(query)
    return dict(user_row._mapping)


async def get_wallet(user_id: int) -> Dict:
    query = wallets.select().where(wallets.c.user_id == user_id)
    wallet_row = await database.fetch_one(query)
    return dict(wallet_row._mapping)


async def get_transaction(wallet_id: int, type_: TransactionType = None) -> Dict:
    query = transactions.select().where(transactions.c.wallet_id == wallet_id)
    if type_ is not None:
        query = query.where(transactions.c.type == type_)
    wallet_row = await database.fetch_one(query)
    return dict(wallet_row._mapping)


@database.transaction()
async def create_transaction(to_user_id: int, amount: str, from_user_id: int = None) -> Transaction:
    """Performs deposit and transfer operation"""
    amt = Decimal(amount)
    if amt <= 0:
        raise ValueError(f'Amount should be positive. Given value {amount}')
    if from_user_id is not None and from_user_id == to_user_id:
        raise ValueError(f'Cannot perform operation for the same user {from_user_id}')
    to_wallet_id = None
    from_wallet_id = None
    # Lock wallets involved in operation
    if from_user_id is None:
        query = select([wallets.c.id]).where(wallets.c.user_id == to_user_id).with_for_update()
        to_wallet_id = await database.execute(query)
        if to_wallet_id is None:
            raise ValueError(f'Cannot find wallet of user {to_user_id} to perform deposit')
    else:
        from_wallet_balance = None
        query = select(wallets).where(wallets.c.user_id.in_([from_user_id, to_user_id])).with_for_update()
        for row in await database.fetch_all(query):
            row_dict = dict(row._mapping)
            if row_dict['user_id'] == to_user_id:
                to_wallet_id = row_dict['id']
            else:
                from_wallet_id = row_dict['id']
                from_wallet_balance = row_dict['balance']
        if to_wallet_id is None:
            raise ValueError(f'Cannot find wallet of user {to_user_id} to perform deposit')
        if from_wallet_id is None:
            raise ValueError(f'Cannot find wallet of user {from_user_id} to perform credit')
        else:
            if from_wallet_balance - amt < 0:
                raise ValueError(
                    f'Not enough money on user {from_user_id} account. Balance {from_wallet_balance}. Amount {amt}')
    # Insert transactions
    credit_id = None
    from_balance = None
    if from_user_id is not None:
        debit_id = await insert_transaction(wallet_id=to_wallet_id, type=TransactionType.debit, amount=amt)
        credit_id = await insert_transaction(wallet_id=from_wallet_id, type=TransactionType.credit, amount=amt)
        to_balance = await update_balance(user_id=to_user_id, amount=amt)
        from_balance = await update_balance(user_id=from_user_id, amount=-amt)
    else:
        debit_id = await insert_transaction(wallet_id=to_wallet_id, type=TransactionType.debit, amount=amt)
        to_balance = await update_balance(user_id=to_user_id, amount=amt)
    return Transaction(debit_transaction_id=debit_id, credit_transaction_id=credit_id)
