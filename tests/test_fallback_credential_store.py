"""Tests for FallbackCredentialStore.

Verifies that credentials fall back to local JSON files when keyring
storage fails (e.g., Windows Credential Manager size limit exceeded).
"""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from google.oauth2.credentials import Credentials

from auth.credential_store import (
    FallbackCredentialStore,
    KeyringCredentialStore,
    LocalDirectoryCredentialStore,
)


def _make_credentials(num_scopes: int = 22) -> Credentials:
    """Create a realistic Credentials object with many scopes."""
    scopes = [f"https://www.googleapis.com/auth/scope_{i}" for i in range(num_scopes)]
    return Credentials(
        token="ya29.fake-access-token-value",
        refresh_token="1//fake-refresh-token-value",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="123456789.apps.googleusercontent.com",
        client_secret="GOCSPX-fake-client-secret",
        scopes=scopes,
        expiry=datetime.utcnow() + timedelta(hours=1),
    )


class TestFallbackWhenKeyringFails:
    """Test that credentials fall back to local storage on keyring failure."""

    def test_store_falls_back_to_local_on_keyring_exception(self, tmp_path):
        """If keyring.set_password raises, credentials go to local JSON."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)
        store._keyring_store.store_credential.return_value = False

        creds = _make_credentials()
        result = store.store_credential("user@example.com", creds)

        assert result is True
        assert "user@example.com" in store._local_fallback_users
        # Verify the file was actually written
        assert os.path.exists(tmp_path / "user@example.com.json")

    def test_store_falls_back_on_verification_failure(self, tmp_path):
        """If keyring reports success but read-back doesn't match (silent truncation)."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)

        creds = _make_credentials()

        # Keyring says it stored successfully...
        store._keyring_store.store_credential.return_value = True
        # ...but read-back returns a credential with a different refresh token (truncated)
        corrupted = MagicMock()
        corrupted.refresh_token = "CORRUPTED"
        store._keyring_store.get_credential.return_value = corrupted

        result = store.store_credential("user@example.com", creds)

        assert result is True
        assert "user@example.com" in store._local_fallback_users
        assert os.path.exists(tmp_path / "user@example.com.json")

    def test_get_credential_checks_local_after_fallback(self, tmp_path):
        """After a fallback, get_credential reads from local, not keyring."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)
        store._keyring_store.store_credential.return_value = False

        creds = _make_credentials()
        store.store_credential("user@example.com", creds)

        # Now retrieve — should come from local, not keyring
        loaded = store.get_credential("user@example.com")
        assert loaded is not None
        assert loaded.refresh_token == creds.refresh_token
        # Keyring get_credential should NOT have been called since user is in fallback set
        store._keyring_store.get_credential.assert_not_called()


class TestFallbackWhenKeyringSucceeds:
    """Test that keyring is preferred when it works."""

    def test_store_uses_keyring_when_verification_passes(self, tmp_path):
        """If keyring stores and verifies OK, local storage is not used."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)

        creds = _make_credentials()
        store._keyring_store.store_credential.return_value = True
        # Read-back matches
        store._keyring_store.get_credential.return_value = creds

        result = store.store_credential("user@example.com", creds)

        assert result is True
        assert "user@example.com" not in store._local_fallback_users
        # Local file should NOT have been written
        assert not os.path.exists(tmp_path / "user@example.com.json")

    def test_get_credential_uses_keyring_first(self, tmp_path):
        """When user hasn't fallen back, get_credential checks keyring first."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)

        creds = _make_credentials()
        store._keyring_store.get_credential.return_value = creds

        loaded = store.get_credential("user@example.com")
        assert loaded is not None
        assert loaded.refresh_token == creds.refresh_token
        store._keyring_store.get_credential.assert_called_once_with("user@example.com")


class TestDeleteAndListUsers:
    """Test delete and list_users across both stores."""

    def test_delete_clears_both_stores(self, tmp_path):
        """delete_credential removes from keyring AND local."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)
        store._keyring_store.store_credential.return_value = False
        store._keyring_store.delete_credential.return_value = True

        creds = _make_credentials()
        store.store_credential("user@example.com", creds)
        assert os.path.exists(tmp_path / "user@example.com.json")

        result = store.delete_credential("user@example.com")
        assert result is True
        assert not os.path.exists(tmp_path / "user@example.com.json")
        assert "user@example.com" not in store._local_fallback_users
        store._keyring_store.delete_credential.assert_called_once_with("user@example.com")

    def test_list_users_merges_both_stores(self, tmp_path):
        """list_users returns the union of keyring and local users."""
        store = FallbackCredentialStore()
        store._local_store = LocalDirectoryCredentialStore(base_dir=str(tmp_path))
        store._keyring_store = MagicMock(spec=KeyringCredentialStore)

        store._keyring_store.list_users.return_value = ["alice@example.com", "shared@example.com"]

        # Write a local credential
        store._keyring_store.store_credential.return_value = False
        creds = _make_credentials()
        store.store_credential("bob@example.com", creds)
        store.store_credential("shared@example.com", creds)

        users = store.list_users()
        assert users == ["alice@example.com", "bob@example.com", "shared@example.com"]
