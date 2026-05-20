from dataclasses import dataclass

@dataclass
class TransferMoneyCommand:
    idempotency_key: str
    source_wallet_id: str
    target_wallet_id: str
    amount: float
    currency: str

@dataclass
class TransferMoneyResponse:
    success: bool
    transaction_id: str | None = None
    error: str | None = None
    balance_after_transfer: float | None = None
