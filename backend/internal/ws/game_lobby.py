import abc

__all__ = (
    "GameLobbyBase",
)

class GameLobbyBase(abc.ABC):
    
    @property
    @abc.abstractmethod
    def endpoint(self) -> str:
        """Returns the endpoint name"""
    