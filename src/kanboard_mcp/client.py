"""Kanboard API client wrapper with error handling and retry logic."""

import json
import time
from typing import Any, Dict, Optional, Union
import logging
from urllib.error import HTTPError

import kanboard

from .config import Config


logger = logging.getLogger(__name__)


class KanboardClientError(Exception):
    """Base exception for Kanboard client errors."""
    pass


class KanboardConnectionError(KanboardClientError):
    """Exception raised when connection to Kanboard fails."""
    pass


class KanboardAuthenticationError(KanboardClientError):
    """Exception raised when authentication fails."""
    pass


class KanboardAPIError(KanboardClientError):
    """Exception raised when API call fails."""

    def __init__(self, message: str, code: Optional[int] = None):
        self.code = code
        self.message = message
        if code is None:
            super().__init__(message)
        else:
            super().__init__(f"JSON-RPC error {code}: {message}")


class KanboardClient:
    """Enhanced Kanboard client with error handling and retry logic."""

    def __init__(self, config: Config):
        """Initialize the Kanboard client with configuration."""
        self.config = config
        self._client: Optional[kanboard.Client] = None
        self._connected = False

    def _create_client(self) -> kanboard.Client:
        """Create a new Kanboard client instance."""
        try:
            client = kanboard.Client(
                url=self.config.kanboard.url,
                username=self.config.kanboard.username,
                password=self.config.kanboard.password,
                auth_header=self.config.kanboard.auth_header or 'Authorization',
                insecure=not self.config.kanboard.verify_ssl,
            )
            client._parse_response = self._parse_response_with_error_details
            return client
        except Exception as e:
            logger.error(f"Failed to create Kanboard client: {e}")
            raise KanboardConnectionError(f"Failed to create Kanboard client: {e}")

    @staticmethod
    def _parse_response_with_error_details(response: bytes) -> Any:
        """Parse JSON-RPC responses without discarding error code details."""
        if not response:
            raise KanboardAPIError("Empty response from server")
        try:
            body = json.loads(response.decode(errors="ignore"))
        except ValueError as e:
            raise KanboardAPIError(f"Failed to parse JSON response: {e}")

        error = body.get("error")
        if error:
            if isinstance(error, dict):
                raise KanboardAPIError(
                    error.get("message", "Unknown Kanboard API error"),
                    code=error.get("code"),
                )
            raise KanboardAPIError(str(error))

        return body.get("result")

    def connect(self) -> None:
        """Connect to Kanboard and validate credentials."""
        if self._connected and self._client:
            return

        try:
            self._client = self._create_client()
            # Test connection by calling getMe
            result = self._client.get_me()
            if result is None:
                raise KanboardAuthenticationError("Authentication failed - invalid credentials")

            self._connected = True
            logger.info(f"Connected to Kanboard as user: {result.get('name', 'Unknown')}")

        except kanboard.ClientError as e:
            logger.error(f"Kanboard API error during connection: {e}")
            raise KanboardAuthenticationError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            raise KanboardConnectionError(f"Connection failed: {e}")

    def disconnect(self) -> None:
        """Disconnect from Kanboard."""
        self._client = None
        self._connected = False
        logger.info("Disconnected from Kanboard")

    def is_connected(self) -> bool:
        """Check if client is connected to Kanboard."""
        return self._connected and self._client is not None

    def _execute_with_retry(self, method_name: str, *args, **kwargs) -> Any:
        """Execute a Kanboard API method with retry logic."""
        if not self.is_connected():
            self.connect()

        last_exception = None

        for attempt in range(self.config.server.max_retries + 1):
            try:
                if not self._client:
                    raise KanboardConnectionError("Client not connected")

                method = getattr(self._client, method_name)
                result = method(*args, **kwargs)

                # Log successful call in debug mode
                if self.config.server.debug:
                    logger.debug(f"API call {method_name} succeeded on attempt {attempt + 1}")

                return result

            except KanboardAPIError:
                raise
            except HTTPError as e:
                last_exception = e
                if 400 <= e.code < 500:
                    if e.code == 401:
                        raise KanboardAuthenticationError(f"Authentication failed: {e}")
                    raise KanboardAPIError(f"API error: {e}", code=e.code)
                logger.warning(f"HTTP error in {method_name} (attempt {attempt + 1}): {e}")
            except kanboard.ClientError as e:
                last_exception = e
                error_message = str(e)

                if "HTTP Error 401" in error_message:
                    raise KanboardAuthenticationError(f"Authentication failed: {e}")
                if "HTTP Error 403" in error_message:
                    raise KanboardAPIError(f"API error: {e}", code=403)
                if "HTTP Error 404" in error_message:
                    raise KanboardAPIError(f"API error: {e}", code=404)

                logger.warning(f"API error in {method_name} (attempt {attempt + 1}): {e}")

                # Don't retry on authentication errors
                if "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
                    raise KanboardAuthenticationError(f"Authentication failed: {e}")

                # Don't retry on client errors (4xx)
                if hasattr(e, 'code') and 400 <= e.code < 500:
                    raise KanboardAPIError(f"API error: {e}")

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in {method_name} (attempt {attempt + 1}): {e}")

            # Wait before retrying (except on last attempt)
            if attempt < self.config.server.max_retries:
                time.sleep(self.config.server.retry_delay)

        # All retries exhausted
        if last_exception:
            if isinstance(last_exception, kanboard.ClientError):
                raise KanboardAPIError(f"API call {method_name} failed after {self.config.server.max_retries + 1} attempts: {last_exception}")
            elif isinstance(last_exception, kanboard.ClientError):
                raise KanboardConnectionError(f"Connection failed for {method_name} after {self.config.server.max_retries + 1} attempts: {last_exception}")
            else:
                raise KanboardClientError(f"Unexpected error in {method_name} after {self.config.server.max_retries + 1} attempts: {last_exception}")

        raise KanboardClientError(f"Method {method_name} failed after {self.config.server.max_retries + 1} attempts")

    def call_api(self, method_name: str, *args, **kwargs) -> Any:
        """Call a Kanboard API method with error handling and retry logic."""
        try:
            return self._execute_with_retry(method_name, *args, **kwargs)
        except (KanboardClientError, KanboardAPIError, KanboardAuthenticationError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {method_name}: {e}")
            raise KanboardClientError(f"Unexpected error: {e}")

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Kanboard and return user info."""
        try:
            result = self.call_api(method_name="get_me")
            return {
                "connected": True,
                "user": result,
                "server_url": self.config.kanboard.url,
                "username": self.config.kanboard.username,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "server_url": self.config.kanboard.url,
                "username": self.config.kanboard.username,
            }

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        try:
            user_info = self.call_api(method_name="get_me")
            version = self.call_api(method_name="get_version")

            return {
                "server_version": version,
                "user_info": user_info,
                "api_url": self.config.kanboard.url,
                "connected": True,
            }
        except Exception as e:
            return {
                "server_version": None,
                "user_info": None,
                "api_url": self.config.kanboard.url,
                "connected": False,
                "error": str(e),
            }

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def create_client(config: Config) -> KanboardClient:
    """Create a new Kanboard client instance."""
    return KanboardClient(config)
