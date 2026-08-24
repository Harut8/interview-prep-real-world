import pytest
from app import VendingMachine


@pytest.fixture
def machine():
    m = VendingMachine()
    m.add_product("cola", 1.50, 3)
    m.add_product("chips", 2.00, 2)
    return m


class TestBasicPurchase:
    def test_buy_product(self, machine):
        machine.insert_money(2.00)
        result = machine.select_product("cola")
        assert "dispensed" in result.lower() or "success" in result.lower()

    def test_insufficient_funds(self, machine):
        machine.insert_money(0.50)
        result = machine.select_product("cola")
        assert "insufficient" in result.lower() or "not enough" in result.lower()

    def test_out_of_stock(self, machine):
        for _ in range(3):
            machine.insert_money(2.00)
            machine.select_product("cola")
            machine.get_change()
        machine.insert_money(2.00)
        result = machine.select_product("cola")
        assert "out" in result.lower() or "stock" in result.lower()

    def test_invalid_product(self, machine):
        machine.insert_money(5.00)
        result = machine.select_product("water")
        assert "not found" in result.lower() or "invalid" in result.lower()


class TestMoney:
    def test_get_change(self, machine):
        machine.insert_money(5.00)
        machine.select_product("cola")  # 1.50
        change = machine.get_change()
        assert abs(change - 3.50) < 0.01

    def test_no_purchase_full_refund(self, machine):
        machine.insert_money(3.00)
        change = machine.get_change()
        assert abs(change - 3.00) < 0.01

    def test_change_resets(self, machine):
        machine.insert_money(5.00)
        machine.get_change()
        assert machine.get_change() == 0.0

    def test_accumulate_money(self, machine):
        machine.insert_money(1.00)
        machine.insert_money(1.00)
        result = machine.select_product("cola")
        assert "dispensed" in result.lower() or "success" in result.lower()


class TestInventory:
    def test_inventory_shows_products(self, machine):
        inv = machine.get_inventory()
        assert "cola" in inv
        assert inv["cola"]["quantity"] == 3

    def test_quantity_decreases(self, machine):
        machine.insert_money(2.00)
        machine.select_product("cola")
        inv = machine.get_inventory()
        assert inv["cola"]["quantity"] == 2

    def test_restock(self, machine):
        machine.add_product("cola", 1.50, 5)
        inv = machine.get_inventory()
        assert inv["cola"]["quantity"] == 8
