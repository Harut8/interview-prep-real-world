class BigNum:
    def __init__(self, value: str) -> None:
        pass

    def add(self, other: "BigNum") -> "BigNum":
        raise NotImplementedError

    def subtract(self, other: "BigNum") -> "BigNum":
        raise NotImplementedError

    def multiply(self, other: "BigNum") -> "BigNum":
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        raise NotImplementedError
