import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client(tmp_path, redis_client):
    settings = Settings(database_url=f"sqlite:///{tmp_path}/test.db", environment="test")
    app = create_app(settings=settings, redis_client=redis_client)
    with TestClient(app) as c:
        yield c
