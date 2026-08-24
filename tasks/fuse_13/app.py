class VendingMachine:
    def __init__(self) -> None:
        pass

    def add_product(self, name: str, price: float, quantity: int) -> None:
        raise NotImplementedError

    def insert_money(self, amount: float) -> None:
        raise NotImplementedError

    def select_product(self, name: str) -> str:
        raise NotImplementedError

    def get_change(self) -> float:
        raise NotImplementedError

    def get_inventory(self) -> dict[str, dict]:
        raise NotImplementedError
