from datetime import datetime

import pytest
from google.oauth2.credentials import Credentials

from auth.credential_store import LocalDirectoryCredentialStore


def _credentials() -> Credentials:
    return Credentials(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"],
        expiry=datetime(2030, 1, 1, 0, 0, 0),
    )


def test_local_directory_store_round_trips_credentials(tmp_path):
    store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))

    assert store.store_credential("user@example.com", _credentials()) is True

    restored = store.get_credential("user@example.com")
    assert restored is not None
    assert restored.token == "access-token"
    assert restored.refresh_token == "refresh-token"
    assert restored.client_id == "client-id"
    assert restored.scopes == ["https://www.googleapis.com/auth/drive.metadata.readonly"]
    assert store.list_users() == ["user@example.com"]


def test_local_directory_store_lists_users_from_expanded_base_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    store = LocalDirectoryCredentialStore(base_dir="~/credentials")

    assert store.store_credential("user@example.com", _credentials()) is True
    assert store.list_users() == ["user@example.com"]


@pytest.mark.parametrize(
    "user_email",
    [
        "",
        "../escape",
        "nested/user@example.com",
        r"nested\user@example.com",
    ],
)
def test_local_directory_store_rejects_path_like_user_names(tmp_path, user_email):
    store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))

    with pytest.raises(ValueError):
        store.store_credential(user_email, _credentials())
