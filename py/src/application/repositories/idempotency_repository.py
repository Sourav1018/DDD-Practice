from abc import ABC, abstractmethod
from src.application.dtos.transfer_dto import TransferMoneyResponse

class IdempotencyRepository(ABC):
    @abstractmethod
    def find(self, key: str) -> TransferMoneyResponse | None:
        pass

    @abstractmethod
    def save(self, key: str, response: TransferMoneyResponse) -> None:
        pass
