import uuid
from src.domain.entities.wallet import Wallet
from src.domain.entities.transaction import Transaction
from src.domain.value_objects.money import Money

class TransferService:
    def transfer(self, source: Wallet, target: Wallet, amount: Money) -> Transaction:
        if source.id == target.id:
            raise ValueError("Source and target wallets must be different.")

        # Debit source
        source.debit(amount)

        # Credit target
        target.credit(amount)

        # Create and return transaction
        transaction_id = f"tx_{uuid.uuid4().hex[:9]}"
        return Transaction(transaction_id, source.id, target.id, amount)
