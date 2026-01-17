"""
Credential Store API for Google Workspace MCP

This module provides a standardized interface for credential storage and retrieval.
On macOS (the only supported platform), credentials are stored in the system Keychain.
"""

import json
import logging
import os
import platform
from abc import ABC, abstractmethod
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
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            logger.info(f"Created credentials directory: {self.base_dir}")
        return os.path.join(self.base_dir, f"{user_email}.json")

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
        if not os.path.exists(self.base_dir):
            return []

        users = []
        try:
            for filename in os.listdir(self.base_dir):
                if filename.endswith(".json"):
                    user_email = filename[:-5]  # Remove .json extension
                    users.append(user_email)
            logger.debug(
                f"Found {len(users)} users with credentials in {self.base_dir}"
            )
        except OSError as e:
            logger.error(f"Error listing credential files in {self.base_dir}: {e}")

        return sorted(users)


class KeychainCredentialStore(CredentialStore):
    """
    Credential store using macOS Keychain via the keyring library.

    CG-MODIFIED: Added for secure credential storage instead of plaintext JSON files.
    Credentials are stored in the system Keychain, protected by macOS security.
    """

    SERVICE_NAME = "hardened-google-workspace-mcp"
    _USERS_KEY = "__registered_users__"

    def __init__(self):
        """Initialize the Keychain credential store."""
        try:
            import keyring

            self._keyring = keyring
        except ImportError as e:
            raise RuntimeError(
                "keyring package is required for Keychain credential storage. "
                "Install it with: uv add keyring"
            ) from e

        logger.info(
            f"KeychainCredentialStore initialized (service: {self.SERVICE_NAME})"
        )

    def _get_users_set(self) -> set:
        """Get the set of registered users from keychain."""
        try:
            users_json = self._keyring.get_password(self.SERVICE_NAME, self._USERS_KEY)
            if users_json:
                return set(json.loads(users_json))
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Error reading users list from keychain: {e}")
        return set()

    def _save_users_set(self, users: set) -> None:
        """Save the set of registered users to keychain."""
        try:
            self._keyring.set_password(
                self.SERVICE_NAME, self._USERS_KEY, json.dumps(sorted(users))
            )
        except Exception as e:
            logger.error(f"Error saving users list to keychain: {e}")

    def get_credential(self, user_email: str) -> Optional[Credentials]:
        """Get credentials from macOS Keychain."""
        try:
            creds_json = self._keyring.get_password(self.SERVICE_NAME, user_email)
            if not creds_json:
                logger.debug(f"No credentials found in keychain for {user_email}")
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

            logger.debug(f"Loaded credentials for {user_email} from keychain")
            return credentials

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding credentials for {user_email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving credentials for {user_email}: {e}")
            return None

    def store_credential(self, user_email: str, credentials: Credentials) -> bool:
        """Store credentials to macOS Keychain."""
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

            logger.info(f"Stored credentials for {user_email} in keychain")
            return True

        except Exception as e:
            logger.error(f"Error storing credentials for {user_email}: {e}")
            return False

    def delete_credential(self, user_email: str) -> bool:
        """Delete credentials from macOS Keychain."""
        try:
            self._keyring.delete_password(self.SERVICE_NAME, user_email)

            # Update users list
            users = self._get_users_set()
            users.discard(user_email)
            self._save_users_set(users)

            logger.info(f"Deleted credentials for {user_email} from keychain")
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
        logger.debug(f"Found {len(users)} users with credentials in keychain")
        return sorted(users)


# Global credential store instance
_credential_store: Optional[CredentialStore] = None


def get_credential_store() -> CredentialStore:
    """
    Get the global credential store instance.

    CG-MODIFIED: macOS-only with Keychain storage for security.

    Returns:
        Configured credential store instance

    Raises:
        RuntimeError: If not running on macOS
    """
    global _credential_store

    if _credential_store is None:
        if platform.system() != "Darwin":
            raise RuntimeError(
                "This MCP server only supports macOS. "
                "Credential storage requires macOS Keychain."
            )
        _credential_store = KeychainCredentialStore()
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
