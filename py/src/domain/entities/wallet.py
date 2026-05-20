from src.domain.value_objects.money import Money

class Wallet:
    def __init__(self, wallet_id: str, balance: Money, version: int = 0):
        self._id = wallet_id
        self._balance = balance
        self._version = version

    @property
    def id(self) -> str:
        return self._id

    @property
    def balance(self) -> Money:
        return self._balance

    @property
    def version(self) -> int:
        return self._version

    def debit(self, amount: Money) -> None:
        """
        Debits money from the wallet. Enforces the business rule that balance cannot drop below zero.
        """
        if not self._balance.is_greater_than_or_equal(amount):
            raise ValueError(
                f"Insufficient funds: Wallet {self._id} has {self._balance.amount} {self._balance.currency.code}, "
                f"requested {amount.amount}"
            )
        self._balance = self._balance.subtract(amount)

    def credit(self, amount: Money) -> None:
        """
        Credits money to the wallet.
        """
        self._balance = self._balance.add(amount)

    def increment_version(self) -> None:
        """
        Increments the entity version for optimistic locking.
        """
        self._version += 1

    def __repr__(self) -> str:
        return f"Wallet({self._id}, Balance: {self._balance.amount} {self._balance.currency.code}, Version: {self._version})"
