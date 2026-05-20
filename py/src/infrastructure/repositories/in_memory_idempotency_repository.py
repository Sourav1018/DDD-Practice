from src.application.dtos.transfer_dto import TransferMoneyResponse
from src.application.repositories.idempotency_repository import IdempotencyRepository

class InMemoryIdempotencyRepository(IdempotencyRepository):
    def __init__(self):
        self._cache: dict[str, TransferMoneyResponse] = {}

    def find(self, key: str) -> TransferMoneyResponse | None:
        response = self._cache.get(key)
        if response:
            # Return a copy to mimic DB retrieval isolation
            return TransferMoneyResponse(
                success=response.success,
                transaction_id=response.transaction_id,
                error=response.error,
                balance_after_transfer=response.balance_after_transfer
            )
        return None

    def save(self, key: str, response: TransferMoneyResponse) -> None:
        self._cache[key] = response

    def clear(self) -> None:
        self._cache.clear()
