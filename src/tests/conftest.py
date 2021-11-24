import pytest

from src.main.model import UserRequest


@pytest.fixture
def sample_user1():
    return UserRequest(first_name='first_name1', last_name='last_name1')


@pytest.fixture
def sample_user2():
    return UserRequest(first_name='first_name2', last_name='last_name2')
