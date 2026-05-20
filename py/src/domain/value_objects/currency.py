class Currency:
    def __init__(self, code: str):
        clean_code = code.strip().upper()
        if len(clean_code) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code.")
        
        supported = {"USD", "EUR", "INR"}
        if clean_code not in supported:
            raise ValueError(f"Unsupported currency code: {clean_code}. Supported: {', '.join(supported)}")
        
        self._code = clean_code

    @property
    def code(self) -> str:
        return self._code

    def equals(self, other: 'Currency') -> bool:
        if not isinstance(other, Currency):
            return False
        return self._code == other.code

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Currency):
            return NotImplemented
        return self.equals(other)

    def __repr__(self) -> str:
        return f"Currency({self._code})"
