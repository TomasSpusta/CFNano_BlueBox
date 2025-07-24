from abc import ABC, abstractmethod
from app_context import AppContext


class State(ABC):
    """
    Base state. Teplate for other states.
    """

    @abstractmethod
    async def run(self, context: AppContext) -> "State":
        pass
