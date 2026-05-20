import time
from src.domain.entities.wallet import Wallet
from src.domain.repositories.wallet_repository import WalletRepository
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money

class ConcurrencyError(Exception):
    pass

class WalletRecord:
    def __init__(self, wallet_id: str, amount: float, currency_code: str, version: int):
        self.id = wallet_id
        self.amount = amount
        self.currency_code = currency_code
        self.version = version

class InMemoryWalletRepository(WalletRepository):
    def __init__(self, use_optimistic_locking: bool = True, simulated_delay_seconds: float = 0.0):
        self._records: dict[str, WalletRecord] = {}
        self.use_optimistic_locking = use_optimistic_locking
        self.simulated_delay_seconds = simulated_delay_seconds

    def find_by_id(self, wallet_id: str) -> Wallet | None:
        record = self._records.get(wallet_id)
        if not record:
            return None
        
        currency = Currency(record.currency_code)
        balance = Money(record.amount, currency)
        return Wallet(record.id, balance, record.version)

    def save(self, wallet: Wallet) -> None:
        # 1. Simulate DB latency
        if self.simulated_delay_seconds > 0.0:
            time.sleep(self.simulated_delay_seconds)

        current_record = self._records.get(wallet.id)
        if not current_record:
            # First time save
            self._records[wallet.id] = WalletRecord(
                wallet_id=wallet.id,
                amount=wallet.balance.amount,
                currency_code=wallet.balance.currency.code,
                version=wallet.version
            )
            return

        # 2. Check version for optimistic locking
        if self.use_optimistic_locking:
            if current_record.version != wallet.version:
                raise ConcurrencyError(
                    f"Optimistic locking conflict: Wallet {wallet.id} was updated by another request. "
                    f"Current DB version: {current_record.version}, wallet version: {wallet.version}"
                )
            
            # Successful write: increment version
            new_version = current_record.version + 1
            current_record.amount = wallet.balance.amount
            current_record.currency_code = wallet.balance.currency.code
            current_record.version = new_version
            
            # Synchronize the aggregate root in-memory version
            wallet.increment_version()
        else:
            # Overwrite without checks
            current_record.amount = wallet.balance.amount
            current_record.currency_code = wallet.balance.currency.code

    def seed(self, wallet_id: str, amount: float, currency_code: str) -> None:
        self._records[wallet_id] = WalletRecord(
            wallet_id=wallet_id,
            amount=amount,
            currency_code=currency_code,
            version=0
        )

    def clear(self) -> None:
        self._records.clear()
