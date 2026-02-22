# My Solution — Task 21

## Bug Fixes

### 1. `delete(n)` — n=0 and negative values

Both lines have the `[:-0]` bug. `[:-0]` evaluates to `[:0]` which gives `[]`, wiping the buffer.

Fix: guard both lines for `n=0` (no-op) and reject `n < 0`.

```python
def delete(self, n: int) -> str:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return ""
    deleted = self._content[-n:]
    self._content = self._content[:-n]
    self._cursor_pos = len(self._content)
    self._cache = None  # invalidate cache
    return "".join(deleted)
```

### 2. `insert_at(pos, text)` — no bounds checking

If `pos > len(content)` — clamp to end. If `pos < 0` — raise error.

```python
def insert_at(self, pos: int, text: str) -> None:
    if pos < 0:
        raise ValueError("Position cannot be negative")
    pos = min(pos, len(self._content))  # clamp to end
    for i, char in enumerate(text):
        self._content.insert(pos + i, char)
    self._cursor_pos = pos + len(text)
    self._cache = None
```

### 3. `get_content()` — inefficient, rebuilds string every call

Use a simple dirty-flag cache. Set `self._cache = None` in every mutating method (`append`, `delete`, `insert_at`). Rebuild only when needed.

```python
def __init__(self, initial_text: str = ""):
    self._content = list(initial_text)
    self._cursor_pos = len(self._content)
    self._cache = None

def get_content(self) -> str:
    if self._cache is None:
        self._cache = "".join(self._content)
    return self._cache
```

Every mutating method must do `self._cache = None`.

### 4. `find(query)` — only returns first match

Loop with `str.find(sub, start)`, advancing start past each match until `-1`.

```python
def find(self, query: str) -> list[int]:
    content = self.get_content()
    positions = []
    start = 0
    while True:
        pos = content.find(query, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1  # +1 to allow overlapping matches
    return positions
```

---

## Feature Implementation Plan

### Feature 1 & 2: `undo()` / `redo()` — Command Pattern

Use the **command pattern**. Each mutating operation creates a command object that knows how to execute and reverse itself.

```
class Command(ABC):
    @abstractmethod
    def execute(self, buffer): ...
    @abstractmethod
    def undo(self, buffer): ...

class AppendCommand(Command):
    # stores text; undo = delete last len(text) chars

class DeleteCommand(Command):
    # stores deleted text + original length; undo = append deleted text back

class InsertAtCommand(Command):
    # stores pos + text; undo = remove len(text) chars starting at pos
```

Buffer keeps two stacks:
- `self._undo_stack: list[Command]` — push after each operation
- `self._redo_stack: list[Command]` — push when undo is called, clear on new operation

```python
def undo(self):
    if not self._undo_stack:
        return
    cmd = self._undo_stack.pop()
    cmd.undo(self)
    self._redo_stack.append(cmd)

def redo(self):
    if not self._redo_stack:
        return
    cmd = self._redo_stack.pop()
    cmd.execute(self)
    self._undo_stack.append(cmd)
```

New operations clear `self._redo_stack` (can't redo after a new action).

### Feature 3: `Cursor` class

Separate class that holds position and references the buffer for bounds checking.

```python
class Cursor:
    def __init__(self, buffer: TextBuffer):
        self._buffer = buffer
        self._pos = 0

    def move_to(self, pos: int):
        # clamp to [0, buffer.length()]
        self._pos = max(0, min(pos, self._buffer.length()))

    def move_left(self, n: int = 1):
        self._pos = max(0, self._pos - n)

    def move_right(self, n: int = 1):
        self._pos = min(self._buffer.length(), self._pos + n)

    @property
    def position(self) -> int:
        return self._pos
```

### Feature 4: `type_at_cursor(text)`

Inserts text at current cursor position, advances cursor past inserted text.

```python
def type_at_cursor(self, text: str) -> None:
    self.insert_at(self._cursor.position, text)
    self._cursor.move_to(self._cursor.position)  # already updated by insert_at
```

This should also push an `InsertAtCommand` for undo support.

### Feature 5: `select(start, end)` and `delete_selection()`

Store selection as a range on the Cursor (or buffer).

```python
class Cursor:
    def __init__(self, buffer):
        self._pos = 0
        self._selection_start = None
        self._selection_end = None

    def select(self, start: int, end: int):
        # validate: 0 <= start <= end <= buffer.length()
        self._selection_start = max(0, start)
        self._selection_end = min(end, self._buffer.length())

    def clear_selection(self):
        self._selection_start = None
        self._selection_end = None
```

```python
# On TextBuffer:
def delete_selection(self) -> str:
    start = self._cursor._selection_start
    end = self._cursor._selection_end
    if start is None or end is None:
        return ""
    deleted = self._content[start:end]
    self._content = self._content[:start] + self._content[end:]
    self._cursor.clear_selection()
    self._cursor.move_to(start)
    self._cache = None
    return "".join(deleted)
```

Should also push a command for undo support.

### Feature 6: Tests

Cover all bugs and features:
- **delete**: n=0 returns "" and doesn't wipe buffer, n<0 raises ValueError, normal delete works
- **insert_at**: pos<0 raises, pos>length clamps, normal insert works
- **get_content caching**: call twice, verify same result, verify invalidation after mutation
- **find**: no match returns [], single match, multiple matches, overlapping matches
- **undo/redo**: undo append, undo delete (restores text), undo insert_at, multiple undos, redo after undo, redo cleared after new operation
- **Cursor**: move_to clamps, move_left/right at boundaries, move_left/right normal
- **type_at_cursor**: inserts at cursor, cursor advances
- **select + delete_selection**: select range, delete returns correct text, buffer updated, cursor moves to start
