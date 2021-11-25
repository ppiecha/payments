from decimal import Decimal

import pytest

from src.main.crud import create_user, create_transaction, get_wallet, get_user, get_transaction
from src.main.model import UserResponse, DepositRequest, TransferRequest, TransactionType
from src.main.app import database
from src.main.settings import init_db


@pytest.mark.asyncio
async def test_create_client(sample_user1):
    await init_db()
    user = await create_user(request=sample_user1)
    user_row = await get_user(first_name=sample_user1.first_name, last_name=sample_user1.last_name)
    wallet = await get_wallet(user_id=user_row['id'])
    assert list(user.dict().items()) == list(UserResponse(**sample_user1.dict(), user_id=user_row['id'],
                                                          wallet_id=wallet['id']).dict().items())
    await database.disconnect()


@pytest.mark.asyncio
async def test_deposit(sample_user1):
    await init_db()
    to_user = await create_user(request=sample_user1)
    deposit = DepositRequest(user_id=to_user.user_id, amount='1.123')
    transaction = await create_transaction(to_user_id=deposit.user_id, amount=deposit.amount)
    wallet = await get_wallet(user_id=deposit.user_id)
    transaction_row = await get_transaction(wallet_id=deposit.user_id)
    assert transaction_row['type'] == TransactionType.debit
    assert transaction_row['id'] == transaction.debit_transaction_id
    assert wallet['balance'] == Decimal(deposit.amount)
    deposit = DepositRequest(user_id=to_user.user_id, amount='0.877')
    transaction = await create_transaction(to_user_id=deposit.user_id, amount=deposit.amount)
    wallet = await get_wallet(user_id=deposit.user_id)
    assert wallet['balance'] == Decimal('2')
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer(sample_user1, sample_user2):
    await init_db()
    from_user = await create_user(request=sample_user1)
    deposit = DepositRequest(user_id=from_user.user_id, amount='100')
    transaction = await create_transaction(to_user_id=deposit.user_id, amount=deposit.amount)
    to_user = await create_user(request=sample_user2)
    transfer = TransferRequest(from_user_id=from_user.user_id, to_user_id=to_user.user_id, amount='20')
    transaction = await create_transaction(to_user_id=transfer.to_user_id, from_user_id=transfer.from_user_id,
                                           amount=transfer.amount)
    from_wallet = await get_wallet(user_id=transfer.from_user_id)
    to_wallet = await get_wallet(user_id=transfer.to_user_id)
    from_transaction = await get_transaction(wallet_id=from_wallet['id'], type_=TransactionType.credit)
    to_transaction = await get_transaction(wallet_id=to_wallet['id'])
    assert from_transaction['id'] is not None
    assert to_transaction['type'] == TransactionType.debit
    assert from_wallet['balance'] == Decimal('80')
    assert to_wallet['balance'] == Decimal('20')
    await database.disconnect()


@pytest.mark.asyncio
async def test_negative_amount(sample_user1):
    await init_db()
    to_user = await create_user(request=sample_user1)
    with pytest.raises(ValueError):
        deposit = DepositRequest(user_id=to_user.user_id, amount='-1')
        transaction = await create_transaction(to_user_id=deposit.user_id, amount=deposit.amount)
    await database.disconnect()
