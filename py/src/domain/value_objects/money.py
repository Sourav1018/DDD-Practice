from src.domain.value_objects.currency import Currency

class Money:
    def __init__(self, amount: float | int, currency: Currency):
        # Allow ints or floats, but validate decimals
        amount_val = float(amount)
        if amount_val < 0:
            raise ValueError("Money amount cannot be negative.")
        
        # Validate maximum of 2 decimal places to avoid floating point precision issues
        if round(amount_val, 2) != amount_val:
            raise ValueError("Money amount cannot have more than 2 decimal places.")
            
        self._amount = amount_val
        self._currency = currency

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> Currency:
        return self._currency

    @staticmethod
    def zero(currency: Currency) -> 'Money':
        return Money(0, currency)

    def add(self, other: 'Money') -> 'Money':
        self._check_same_currency(other)
        # Prevent floating point anomalies by doing integer round-math
        new_amount = round(self._amount + other.amount, 2)
        return Money(new_amount, self._currency)

    def subtract(self, other: 'Money') -> 'Money':
        self._check_same_currency(other)
        if self._amount < other.amount:
            raise ValueError("Insufficient funds for subtraction.")
        new_amount = round(self._amount - other.amount, 2)
        return Money(new_amount, self._currency)

    def is_greater_than_or_equal(self, other: 'Money') -> bool:
        self._check_same_currency(other)
        return self._amount >= other.amount

    def equals(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount == other.amount and self._currency.equals(other.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.equals(other)

    def _check_same_currency(self, other: 'Money') -> None:
        if not self._currency.equals(other.currency):
            raise ValueError(
                f"Currency mismatch: cannot perform operation between {self._currency.code} and {other.currency.code}"
            )

    def __repr__(self) -> str:
        return f"Money({self._amount}, {self._currency})"
