from decimal import Decimal

import pytest
from httpx import AsyncClient

from src.main.app import app, database
from src.main.model import DepositRequest, wallets, TransferRequest
from src.main.utils.constants import CREATE_USER, TEST_URL, DEPOSIT_MONEY, TRANSFER_MONEY


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url=TEST_URL) as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_user_endpoint(async_client, sample_user1):
    await database.connect()
    response = await async_client.post(url=CREATE_USER, content=sample_user1.json())
    assert response.status_code == 201
    assert list(response.json().keys()) == ['first_name', 'last_name', 'user_id', 'wallet_id']
    assert response.json()['user_id'] is not None
    await database.disconnect()


@pytest.mark.asyncio
async def test_deposit_endpoint(async_client, sample_user1):
    await database.connect()
    user1 = await async_client.post(url=CREATE_USER, content=sample_user1.json())
    deposit_request = DepositRequest(user_id=user1.json()['user_id'], amount='1')
    deposit_response = await async_client.post(url=DEPOSIT_MONEY, content=deposit_request.json())
    assert deposit_response.status_code == 200
    assert dict(deposit_response.json())['debit_transaction_id'] is not None
    deposit_request = DepositRequest(user_id=user1.json()['user_id'], amount='1')
    deposit_response = await async_client.post(url=DEPOSIT_MONEY, content=deposit_request.json())
    assert deposit_response.status_code == 200
    assert dict(deposit_response.json())['debit_transaction_id'] is not None
    query = wallets.select().where(wallets.c.user_id == deposit_request.user_id)
    wallet_row = await database.fetch_one(query)
    assert dict(wallet_row._mapping)['balance'] == Decimal('2')
    await database.disconnect()


@pytest.mark.asyncio
async def test_deposit_bad_user_id(async_client, sample_user1):
    await database.connect()
    deposit_request = DepositRequest(user_id=-1, amount='1')
    with pytest.raises(ValueError):
        deposit_response = await async_client.post(url=DEPOSIT_MONEY, content=deposit_request.json())
        assert deposit_response.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_endpoint(async_client, sample_user1, sample_user2):
    await database.connect()
    user1 = await async_client.post(url=CREATE_USER, content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER, content=sample_user2.json())
    deposit_request = DepositRequest(user_id=user1.json()['user_id'], amount='100')
    deposit_response = await async_client.post(url=DEPOSIT_MONEY, content=deposit_request.json())
    transfer_request = TransferRequest(from_user_id=user1.json()['user_id'], to_user_id=user2.json()['user_id'],
                                       amount='20')
    transfer_response = await async_client.post(url=TRANSFER_MONEY, content=transfer_request.json())
    assert transfer_response.status_code == 200
    assert dict(transfer_response.json())['debit_transaction_id'] is not None
    assert dict(transfer_response.json())['credit_transaction_id'] is not None
    query = wallets.select().where(wallets.c.user_id == deposit_request.user_id)
    wallet_row = await database.fetch_one(query)
    assert dict(wallet_row._mapping)['balance'] == Decimal('80')
    query = wallets.select().where(wallets.c.user_id == transfer_request.to_user_id)
    wallet_row = await database.fetch_one(query)
    assert dict(wallet_row._mapping)['balance'] == Decimal('20')
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_bad_user_id(async_client):
    await database.connect()
    transfer_request = TransferRequest(from_user_id=-1, to_user_id=-2, amount='1')
    with pytest.raises(ValueError):
        transfer_response = await async_client.post(url=TRANSFER_MONEY, content=transfer_request.json())
        assert transfer_response.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_bad_amount(async_client, sample_user1, sample_user2):
    await database.connect()
    user1 = await async_client.post(url=CREATE_USER, content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER, content=sample_user2.json())
    with pytest.raises(ValueError):
        transfer_request = TransferRequest(from_user_id=user1.json()['user_id'], to_user_id=user2.json()['user_id'],
                                           amount='@')
        deposit_response = await async_client.post(url=TRANSFER_MONEY, content=transfer_request.json())
        assert deposit_response.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_not_enough_money(async_client, sample_user1, sample_user2):
    await database.connect()
    user1 = await async_client.post(url=CREATE_USER, content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER, content=sample_user2.json())
    with pytest.raises(ValueError):
        transfer_request = TransferRequest(from_user_id=user1.json()['user_id'], to_user_id=user2.json()['user_id'],
                                           amount='100')
        deposit_response = await async_client.post(url=TRANSFER_MONEY, content=transfer_request.json())
        assert deposit_response.status_code == 500
    await database.disconnect()
