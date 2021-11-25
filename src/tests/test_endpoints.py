from decimal import Decimal

import pytest
from httpx import AsyncClient

from src.main.app import app, database
from src.main.crud import get_wallet
from src.main.model import DepositRequest, TransferRequest
from src.main.settings import init_db
from src.main.utils.constants import CREATE_USER, TEST_URL, DEPOSIT_MONEY, \
    TRANSFER_MONEY


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url=TEST_URL) as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_user_endpoint(async_client, sample_user1):
    await init_db()
    resp = await async_client.post(url=CREATE_USER,
                                   content=sample_user1.json())
    assert resp.status_code == 201
    assert list(resp.json().keys()) == ['first_name', 'last_name',
                                        'user_id', 'wallet_id']
    assert resp.json()['user_id'] is not None
    await database.disconnect()


@pytest.mark.asyncio
async def test_deposit_endpoint(async_client, sample_user1):
    await init_db()
    user1 = await async_client.post(url=CREATE_USER,
                                    content=sample_user1.json())
    deposit_req = DepositRequest(user_id=user1.json()['user_id'],
                                 amount='1')
    deposit_resp = await async_client.post(url=DEPOSIT_MONEY,
                                           content=deposit_req.json())
    assert deposit_resp.status_code == 200
    assert dict(deposit_resp.json())['debit_transaction_id'] is not None
    deposit_resp = await async_client.post(url=DEPOSIT_MONEY,
                                           content=deposit_req.json())
    assert deposit_resp.status_code == 200
    assert dict(deposit_resp.json())['debit_transaction_id'] is not None
    wallet_row = await get_wallet(user_id=deposit_req.user_id)
    assert wallet_row['balance'] == Decimal('2')
    await database.disconnect()


@pytest.mark.asyncio
async def test_deposit_bad_user_id(async_client, sample_user1):
    await init_db()
    deposit_req = DepositRequest(user_id=-1, amount='1')
    with pytest.raises(ValueError):
        deposit_resp = await async_client.post(url=DEPOSIT_MONEY,
                                               content=deposit_req.json())
        assert deposit_resp.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_endpoint(async_client, sample_user1, sample_user2):
    await init_db()
    user1 = await async_client.post(url=CREATE_USER,
                                    content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER,
                                    content=sample_user2.json())
    deposit_req = DepositRequest(user_id=user1.json()['user_id'],
                                 amount='100')
    await async_client.post(url=DEPOSIT_MONEY,
                            content=deposit_req.json())
    transfer_req = TransferRequest(from_user_id=user1.json()['user_id'],
                                   to_user_id=user2.json()['user_id'],
                                   amount='20')
    transfer_resp = await async_client.post(url=TRANSFER_MONEY,
                                            content=transfer_req.json())
    assert transfer_resp.status_code == 200
    assert dict(transfer_resp.json())['debit_transaction_id'] is not None
    assert dict(transfer_resp.json())['credit_transaction_id'] is not None
    wallet_row = await get_wallet(user_id=deposit_req.user_id)
    assert wallet_row['balance'] == Decimal('80')
    wallet_row = await get_wallet(user_id=transfer_req.to_user_id)
    assert wallet_row['balance'] == Decimal('20')
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_bad_user_id(async_client):
    await init_db()
    transfer_req = TransferRequest(from_user_id=-1, to_user_id=-2,
                                   amount='1')
    with pytest.raises(ValueError):
        transfer_resp = await async_client.post(url=TRANSFER_MONEY,
                                                content=transfer_req.json())
        assert transfer_resp.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_bad_amount(async_client, sample_user1, sample_user2):
    await init_db()
    user1 = await async_client.post(url=CREATE_USER,
                                    content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER,
                                    content=sample_user2.json())
    with pytest.raises(ValueError):
        transfer_req = TransferRequest(
            from_user_id=user1.json()['user_id'],
            to_user_id=user2.json()['user_id'],
            amount='@')
        deposit_resp = await async_client.post(url=TRANSFER_MONEY,
                                               content=transfer_req.json())
        assert deposit_resp.status_code == 500
    await database.disconnect()


@pytest.mark.asyncio
async def test_transfer_not_enough_money(async_client, sample_user1,
                                         sample_user2):
    await init_db()
    user1 = await async_client.post(url=CREATE_USER,
                                    content=sample_user1.json())
    user2 = await async_client.post(url=CREATE_USER,
                                    content=sample_user2.json())
    with pytest.raises(ValueError):
        transfer_req = TransferRequest(
            from_user_id=user1.json()['user_id'],
            to_user_id=user2.json()['user_id'],
            amount='100')
        deposit_resp = await async_client.post(url=TRANSFER_MONEY,
                                               content=transfer_req.json())
        assert deposit_resp.status_code == 500
    await database.disconnect()
