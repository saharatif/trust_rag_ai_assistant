import asyncio
import pytest
from src.db.database import init_db


@pytest.fixture(scope="session", autouse=True)
def initialize_db():
    asyncio.get_event_loop().run_until_complete(init_db("sqlite:///:memory:"))
