"""
Credential Store API for Google Workspace MCP

This module provides a standardized interface for credential storage and retrieval.
Credentials are stored in the platform's native credential manager (macOS Keychain,
Windows Credential Manager, or Linux SecretService/KWallet) via the keyring library.

The keyring backend is validated at startup against an allowlist of trusted backends
to prevent silent fallback to plaintext storage.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


class CredentialStore(ABC):
    """Abstract base class for credential storage."""

    @abstractmethod
    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """
        Get credentials for a user by email.

        Args:
            user_email: User's email address

        Returns:
            Google Credentials object or None if not found
        """
        pass

    @abstractmethod
    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """
        Store credentials for a user.

        Args:
            user_email: User's email address
            credentials: Google Credentials object to store

        Returns:
            True if successfully stored, False otherwise
        """
        pass

    @abstractmethod
    def delete_credential(self, user_email: str) -> bool:
        """
        Delete credentials for a user.

        Args:
            user_email: User's email address

        Returns:
            True if successfully deleted, False otherwise
        """
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        """
        List all users with stored credentials.

        Returns:
            List of user email addresses
        """
        pass


class LocalDirectoryCredentialStore(CredentialStore):
    """Credential store that uses local JSON files for storage."""

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the local JSON credential store.

        Args:
            base_dir: Base directory for credential files. If None, uses the directory
                     configured by the GOOGLE_MCP_CREDENTIALS_DIR environment variable,
                     or defaults to ~/.google_workspace_mcp/credentials if the environment
                     variable is not set.
        """
        if base_dir is None:
            if os.getenv("GOOGLE_MCP_CREDENTIALS_DIR"):
                base_dir = os.getenv("GOOGLE_MCP_CREDENTIALS_DIR")
            else:
                home_dir = os.path.expanduser("~")
                if home_dir and home_dir != "~":
                    base_dir = os.path.join(
                        home_dir, ".google_workspace_mcp", "credentials"
                    )
                else:
                    base_dir = os.path.join(os.getcwd(), ".credentials")

        self.base_dir = base_dir
        logger.info(f"LocalJsonCredentialStore initialized with base_dir: {base_dir}")

    def _get_credential_path(self, user_email: str) -> str:
        """Get the file path for a user's credentials."""
        if not user_email or "/" in user_email or "\\" in user_email:
            raise ValueError("Credential user email must be a non-empty file name")

        base_path = self._get_base_path(create=True)

        credential_path = (base_path / f"{user_email}.json").resolve()
        if credential_path.parent != base_path:
            raise ValueError("Credential user email resolves outside credential directory")

        return str(credential_path)

    def _get_base_path(self, create: bool = False) -> Path:
        """Resolve the configured credential directory consistently."""
        base_path = Path(self.base_dir).expanduser().resolve()
        if create and not base_path.exists():
            base_path.mkdir(parents=True)
            logger.info(f"Created credentials directory: {self.base_dir}")
        return base_path

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from local JSON file."""
        creds_path = self._get_credential_path(user_email)

        if not os.path.exists(creds_path):
            logger.debug(f"No credential file found for {user_email} at {creds_path}")
            return None

        try:
            with open(creds_path, "r") as f:
                creds_data = json.load(f)

            # Parse expiry if present
            expiry = None
            if creds_data.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                    # Ensure timezone-naive datetime for Google auth library compatibility
                    if expiry.tzinfo is not None:
                        expiry = expiry.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry time for {user_email}: {e}")

            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes"),
                expiry=expiry,
            )

            logger.debug(f"Loaded credentials for {user_email} from {creds_path}")
            return credentials

        except (IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(
                f"Error loading credentials for {user_email} from {creds_path}: {e}"
            )
            return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to local JSON file."""
        creds_path = self._get_credential_path(user_email)

        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        try:
            with open(creds_path, "w") as f:
                json.dump(creds_data, f, indent=2)
            logger.info(f"Stored credentials for {user_email} to {creds_path}")
            return True
        except IOError as e:
            logger.error(
                f"Error storing credentials for {user_email} to {creds_path}: {e}"
            )
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credential file for a user."""
        creds_path = self._get_credential_path(user_email)

        try:
            if os.path.exists(creds_path):
                os.remove(creds_path)
                logger.info(f"Deleted credentials for {user_email} from {creds_path}")
                return True
            else:
                logger.debug(
                    f"No credential file to delete for {user_email} at {creds_path}"
                )
                return True  # Consider it a success if file doesn't exist
        except IOError as e:
            logger.error(
                f"Error deleting credentials for {user_email} from {creds_path}: {e}"
            )
            return False

    def list_users(self) -> List[str]:
        """List all users with credential files."""
        base_path = self._get_base_path()
        if not base_path.is_dir():
            return []

        users = []
        try:
            for credential_file in base_path.iterdir():
                if credential_file.is_file() and credential_file.name.endswith(".json"):
                    user_email = credential_file.name[:-5]  # Remove .json extension
                    users.append(user_email)
            logger.debug(
                f"Found {len(users)} users with credentials in {base_path}"
            )
        except OSError as e:
            logger.error(f"Error listing credential files in {base_path}: {e}")

        return sorted(users)


class KeyringCredentialStore(CredentialStore):
    """
    Credential store using the platform's native credential manager via keyring.

    CW-MODIFIED: Added for secure credential storage instead of plaintext JSON files.
    Uses macOS Keychain, Windows Credential Manager, or Linux SecretService/KWallet
    depending on the platform.
    """

    SERVICE_NAME = "hardened-google-workspace-mcp"
    _USERS_KEY = "__registered_users__"

    def __init__(self):
        """Initialize the keyring credential store."""
        try:
            import keyring

            self._keyring = keyring
        except ImportError as e:
            raise RuntimeError(
                "keyring package is required for credential storage. "
                "Install it with: uv add keyring"
            ) from e

        logger.info(
            f"KeyringCredentialStore initialized (service: {self.SERVICE_NAME})"
        )

    def _get_users_set(self) -> set:
        """Get the set of registered users from keyring."""
        try:
            users_json = self._keyring.get_password(self.SERVICE_NAME, self._USERS_KEY)
            if users_json:
                return set(json.loads(users_json))
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Error reading users list from keyring: {e}")
        return set()

    def _save_users_set(self, users: set) -> None:
        """Save the set of registered users to keyring."""
        try:
            self._keyring.set_password(
                self.SERVICE_NAME, self._USERS_KEY, json.dumps(sorted(users))
            )
        except Exception as e:
            logger.error(f"Error saving users list to keyring: {e}")

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from keyring."""
        try:
            creds_json = self._keyring.get_password(self.SERVICE_NAME, user_email)
            if not creds_json:
                logger.debug(f"No credentials found in keyring for {user_email}")
                return None

            creds_data = json.loads(creds_json)

            # Parse expiry if present
            expiry = None
            if creds_data.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(creds_data["expiry"])
                    # Ensure timezone-naive datetime for Google auth library compatibility
                    if expiry.tzinfo is not None:
                        expiry = expiry.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse expiry time for {user_email}: {e}")

            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes"),
                expiry=expiry,
            )

            logger.debug(f"Loaded credentials for {user_email} from keyring")
            return credentials

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding credentials for {user_email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving credentials for {user_email}: {e}")
            return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to keyring."""
        creds_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }

        try:
            self._keyring.set_password(
                self.SERVICE_NAME, user_email, json.dumps(creds_data)
            )

            # Update users list
            users = self._get_users_set()
            users.add(user_email)
            self._save_users_set(users)

            logger.info(f"Stored credentials for {user_email} in keyring")
            return True

        except Exception as e:
            logger.error(f"Error storing credentials for {user_email}: {e}")
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credentials from keyring."""
        try:
            self._keyring.delete_password(self.SERVICE_NAME, user_email)

            # Update users list
            users = self._get_users_set()
            users.discard(user_email)
            self._save_users_set(users)

            logger.info(f"Deleted credentials for {user_email} from keyring")
            return True

        except self._keyring.errors.PasswordDeleteError:
            # Password doesn't exist, consider it a success
            logger.debug(f"No credentials to delete for {user_email}")
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials for {user_email}: {e}")
            return False

    def list_users(self) -> List[str]:
        """List all users with stored credentials."""
        users = self._get_users_set()
        logger.debug(f"Found {len(users)} users with credentials in keyring")
        return sorted(users)


# Allowlist of trusted keyring backend classes. Any backend not in this list
# (including keyrings.alt plaintext backends) will be rejected at startup.
_ALLOWED_BACKEND_CLASSES = {
    "keyring.backends.macOS.Keyring",
    "keyring.backends.Windows.WinVaultKeyring",
    "keyring.backends.SecretService.Keyring",
    "keyring.backends.kwallet.DBusKeyring",
    "keyring.backends.chainer.ChainerBackend",
}


def _validate_keyring_backend() -> None:
    """
    Validate that the active keyring backend is trusted.

    CW-MODIFIED: Prevents silent fallback to plaintext storage (e.g. from
    keyrings.alt) by checking the backend against an allowlist.

    Raises:
        RuntimeError: If the active backend is not in the allowlist, or if
            ChainerBackend has no secure inner backends.
    """
    import keyring

    backend = keyring.get_keyring()
    backend_class = f"{type(backend).__module__}.{type(backend).__qualname__}"

    if backend_class not in _ALLOWED_BACKEND_CLASSES:
        raise RuntimeError(
            f"Untrusted keyring backend detected: {backend_class}\n"
            f"Only these backends are allowed: {sorted(_ALLOWED_BACKEND_CLASSES)}\n"
            "This check prevents silent fallback to plaintext credential storage.\n"
            "Ensure a supported credential manager is available (macOS Keychain, "
            "Windows Credential Manager, or Linux SecretService/KWallet)."
        )

    # If ChainerBackend, validate its inner backends too
    if backend_class == "keyring.backends.chainer.ChainerBackend":
        inner_backends = getattr(backend, "backends", None)
        if not inner_backends:
            raise RuntimeError(
                "keyring ChainerBackend has no inner backends available. "
                "No secure credential storage found.\n"
                "Install a supported credential manager (e.g. SecretService or KWallet on Linux)."
            )

        for inner in inner_backends:
            inner_class = f"{type(inner).__module__}.{type(inner).__qualname__}"
            if inner_class not in _ALLOWED_BACKEND_CLASSES:
                raise RuntimeError(
                    f"Untrusted keyring backend in ChainerBackend chain: {inner_class}\n"
                    f"Only these backends are allowed: {sorted(_ALLOWED_BACKEND_CLASSES)}\n"
                    "This check prevents silent fallback to plaintext credential storage.\n"
                    "Remove the keyrings.alt package if installed: uv remove keyrings.alt"
                )

    logger.info(f"Validated keyring backend: {backend_class}")


# Global credential store instance
_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """
    Get the global credential store instance.

    CW-MODIFIED: Uses keyring with backend validation for secure cross-platform
    credential storage. Rejects untrusted backends to prevent plaintext fallback.

    Returns:
        Configured credential store instance

    Raises:
        RuntimeError: If the keyring backend is not trusted
    """
    global _credential_store

    if _credential_store is None:
        _validate_keyring_backend()
        _credential_store = KeyringCredentialStore()
        logger.info(f"Initialized credential store: {type(_credential_store).__name__}")

    return _credential_store


def set_credential_store(store: CredentialStore):
    """
    Set the global credential store instance.

    Args:
        store: Credential store instance to use
    """
    global _credential_store
    _credential_store = store
    logger.info(f"Set credential store: {type(store).__name__}")
