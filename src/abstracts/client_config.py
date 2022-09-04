"""Client Configuration Abstraction."""
from abc import ABC, abstractmethod


class ClientConfiguration(ABC):
    """Base abstraction for managing a clients configuration."""

    @property
    @abstractmethod
    def url(self) -> str:
        """Return the URL the client configuration has."""

    @property
    @abstractmethod
    def active_address(self) -> str:
        """Return the active address from the client configuration."""

    @property
    @abstractmethod
    def addresses(self) -> list[str]:
        """Return all the addresses from the client configuration."""
