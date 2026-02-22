import pytest
from app import TextBuffer


@pytest.fixture
def buffer():
    return TextBuffer()


@pytest.fixture
def hello_buffer():
    return TextBuffer("Hello")


def test_append(buffer):
    buffer.append("Hello")
    assert buffer.get_content() == "Hello"


def test_append_multiple(buffer):
    buffer.append("Hello")
    buffer.append(" World")
    assert buffer.get_content() == "Hello World"


def test_delete(hello_buffer):
    deleted = hello_buffer.delete(3)
    assert deleted == "llo"
    assert hello_buffer.get_content() == "He"


# FAILS — fix delete(0) which empties the buffer instead of being a no-op
def test_delete_zero(hello_buffer):
    deleted = hello_buffer.delete(0)
    assert deleted == ""
    assert hello_buffer.get_content() == "Hello"


def test_delete_negative_rejected(hello_buffer):
    with pytest.raises(ValueError):
        hello_buffer.delete(-1)


def test_insert_at(hello_buffer):
    hello_buffer.insert_at(5, " World")
    assert hello_buffer.get_content() == "Hello World"


# FAILS — fix insert_at to handle out-of-bounds position
def test_insert_at_beyond_length(hello_buffer):
    hello_buffer.insert_at(999, "!")
    assert hello_buffer.get_content() == "Hello!"


# FAILS — fix find to return all positions
def test_find_all_occurrences(buffer):
    buffer.append("abcabcabc")
    positions = buffer.find("abc")
    assert positions == [0, 3, 6]


def test_char_at(hello_buffer):
    assert hello_buffer.char_at(0) == "H"
    assert hello_buffer.char_at(4) == "o"


def test_char_at_out_of_range(hello_buffer):
    with pytest.raises(IndexError):
        hello_buffer.char_at(100)


def test_length(hello_buffer):
    assert hello_buffer.length() == 5


# TODO: Add tests for undo/redo
# TODO: Add tests for Cursor movement
# TODO: Add tests for type_at_cursor
# TODO: Add tests for select and delete_selection
