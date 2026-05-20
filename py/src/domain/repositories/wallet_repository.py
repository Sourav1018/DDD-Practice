from abc import ABC, abstractmethod
from src.domain.entities.wallet import Wallet

class WalletRepository(ABC):
    @abstractmethod
    def find_by_id(self, wallet_id: str) -> Wallet | None:
        pass

    @abstractmethod
    def save(self, wallet: Wallet) -> None:
        pass
