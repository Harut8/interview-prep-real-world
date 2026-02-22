class TextBuffer:
    """A simple text editor buffer with basic operations."""

    def __init__(self, initial_text: str = ""):
        self._content = list(initial_text)
        self._cursor_pos = len(self._content)

    def append(self, text: str) -> None:
        """Append text to the end of the buffer."""
        self._content.extend(list(text))
        self._cursor_pos = len(self._content)

    def delete(self, n: int) -> str:
        """Delete the last n characters and return deleted text."""
        # BUG: when n=0, self._content[:-0] gives [] instead of full list
        # BUG: doesn't validate n — negative values cause wrong behavior
        deleted = self._content[-n:]
        self._content = self._content[:-n]
        self._cursor_pos = len(self._content)
        return "".join(deleted)

    def insert_at(self, pos: int, text: str) -> None:
        """Insert text at the given position."""
        # BUG: no bounds checking on pos
        for i, char in enumerate(text):
            self._content.insert(pos + i, char)
        self._cursor_pos = pos + len(text)

    def get_content(self) -> str:
        """Return the full buffer content as a string."""
        # BUG: inefficient — rebuilds string every call, should cache
        return "".join(self._content)

    def length(self) -> int:
        """Return the length of the buffer."""
        return len(self._content)

    def find(self, query: str) -> int:
        """Find the position of a query string in the buffer."""
        # BUG: only returns first match, should return all positions
        content = self.get_content()
        return content.find(query)

    def get_cursor_position(self) -> int:
        """Return the current cursor position."""
        return self._cursor_pos

    def char_at(self, pos: int) -> str:
        """Return the character at the given position."""
        if 0 <= pos < len(self._content):
            return self._content[pos]
        raise IndexError(f"Position {pos} out of range")


# TODO: Add undo/redo support using command pattern
# TODO: Add Cursor class with movement operations
# TODO: Add type_at_cursor(text) method
# TODO: Add select(start, end) and delete_selection() methods
