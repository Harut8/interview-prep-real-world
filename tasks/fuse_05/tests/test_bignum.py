import pytest
from app import BigNum


class TestAdd:
    def test_simple(self):
        assert BigNum("123").add(BigNum("456")) == BigNum("579")

    def test_carry(self):
        assert BigNum("999").add(BigNum("1")) == BigNum("1000")

    def test_different_lengths(self):
        assert BigNum("99").add(BigNum("1001")) == BigNum("1100")

    def test_zeros(self):
        assert BigNum("0").add(BigNum("0")) == BigNum("0")

    def test_large(self):
        a = "9" * 100
        b = "1"
        expected = "1" + "0" * 100
        assert BigNum(a).add(BigNum(b)) == BigNum(expected)


class TestSubtract:
    def test_simple(self):
        assert BigNum("456").subtract(BigNum("123")) == BigNum("333")

    def test_borrow(self):
        assert BigNum("1000").subtract(BigNum("1")) == BigNum("999")

    def test_result_zero(self):
        assert BigNum("42").subtract(BigNum("42")) == BigNum("0")

    def test_negative_result(self):
        result = BigNum("100").subtract(BigNum("200"))
        assert str(result) == "-100"


class TestMultiply:
    def test_simple(self):
        assert BigNum("12").multiply(BigNum("34")) == BigNum("408")

    def test_by_zero(self):
        assert BigNum("999").multiply(BigNum("0")) == BigNum("0")

    def test_by_one(self):
        assert BigNum("12345").multiply(BigNum("1")) == BigNum("12345")

    def test_large(self):
        assert BigNum("999").multiply(BigNum("999")) == BigNum("998001")

    def test_very_large(self):
        a = "123456789" * 5
        b = "987654321" * 5
        result = BigNum(a).multiply(BigNum(b))
        assert len(str(result)) > 80


class TestNegatives:
    def test_add_negatives(self):
        assert BigNum("-5").add(BigNum("-3")) == BigNum("-8")

    def test_add_mixed(self):
        assert BigNum("-5").add(BigNum("8")) == BigNum("3")

    def test_multiply_negative(self):
        assert BigNum("-3").multiply(BigNum("4")) == BigNum("-12")

    def test_multiply_two_negatives(self):
        assert BigNum("-3").multiply(BigNum("-4")) == BigNum("12")


class TestStr:
    def test_no_leading_zeros(self):
        assert str(BigNum("00042")) == "42"

    def test_zero(self):
        assert str(BigNum("0")) == "0"

    def test_negative_zero(self):
        assert str(BigNum("-0")) == "0"
