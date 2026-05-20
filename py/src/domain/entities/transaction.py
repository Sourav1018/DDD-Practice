from datetime import datetime, timezone
from src.domain.value_objects.money import Money

class Transaction:
    def __init__(
        self,
        transaction_id: str,
        source_wallet_id: str,
        target_wallet_id: str,
        amount: Money,
        timestamp: datetime | None = None
    ):
        self._id = transaction_id
        self._source_wallet_id = source_wallet_id
        self._target_wallet_id = target_wallet_id
        self._amount = amount
        self._timestamp = timestamp or datetime.now(timezone.utc)

    @property
    def id(self) -> str:
        return self._id

    @property
    def source_wallet_id(self) -> str:
        return self._source_wallet_id

    @property
    def target_wallet_id(self) -> str:
        return self._target_wallet_id

    @property
    def amount(self) -> Money:
        return self._amount

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def __repr__(self) -> str:
        return f"Transaction({self._id}, {self._source_wallet_id} -> {self._target_wallet_id}, Amount: {self._amount})"
