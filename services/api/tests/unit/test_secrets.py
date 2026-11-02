import sys
import types

import pytest

from app.config import Settings
from app.secrets import resolve_database_url

pytestmark = pytest.mark.unit


def test_plain_url_untouched():
    s = Settings(database_url="postgresql://u:p@db/x")
    assert resolve_database_url(s) == "postgresql://u:p@db/x"


def test_placeholder_without_vault_untouched():
    s = Settings(database_url="postgresql://u:__VAULT__@db/x", vault_addr=None)
    assert resolve_database_url(s) == "postgresql://u:__VAULT__@db/x"


def test_password_resolved_from_vault(monkeypatch):
    class FakeKV:
        def read_secret_version(self, **_kw):
            return {"data": {"data": {"password": "s3cr3t"}}}

    class FakeClient:
        def __init__(self, url, token):
            self.secrets = types.SimpleNamespace(kv=types.SimpleNamespace(v2=FakeKV()))

    monkeypatch.setitem(sys.modules, "hvac", types.SimpleNamespace(Client=FakeClient))
    s = Settings(database_url="postgresql://u:__VAULT__@db/x", vault_addr="http://vault:8200", vault_token="t")
    assert resolve_database_url(s) == "postgresql://u:s3cr3t@db/x"
