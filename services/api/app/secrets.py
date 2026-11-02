"""Resolve secrets from HashiCorp Vault when it is configured."""
import logging

from .config import Settings

log = logging.getLogger(__name__)


def resolve_database_url(settings: Settings) -> str:
    """Return the DB URL, substituting the password fetched from Vault if available.

    The DATABASE_URL may contain the placeholder ``__VAULT__`` in place of the
    password, e.g. ``postgresql://jobs:__VAULT__@postgres:5432/jobs``.
    """
    url = settings.database_url
    if "__VAULT__" not in url or not settings.vault_addr:
        return url
    import hvac  # imported lazily: only needed when Vault is in use

    client = hvac.Client(url=settings.vault_addr, token=settings.vault_token)
    secret = client.secrets.kv.v2.read_secret_version(
        path=settings.vault_secret_path, mount_point="secret", raise_on_deleted_version=True
    )
    password = secret["data"]["data"]["password"]
    log.info("database credentials loaded from vault", extra={"path": settings.vault_secret_path})
    return url.replace("__VAULT__", password)
