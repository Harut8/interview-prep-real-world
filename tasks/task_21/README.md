# Task 21: Text Editor Buffer — Fix Bugs & Add Undo/Cursor Support

**Time limit: 60 minutes**

## Existing Codebase
A text editor buffer class that supports basic text operations: append, delete, insert at cursor, and content retrieval.

## Problems to Fix
1. The `delete` method breaks when `n=0` — `list[:-0]` gives `[]` instead of keeping the content. Also doesn't reject negative values.
2. The `insert_at` method doesn't validate the position — inserting beyond buffer length crashes.
3. The `get_content` method rebuilds the string on every call instead of caching — inefficient for large buffers.
4. The `find` method returns only the first match instead of all occurrences.

## Features to Implement
1. Add `undo()` — reverts the last operation (append, delete, insert_at). Support multiple undo levels.
2. Add `redo()` — re-applies the last undone operation.
3. Add a `Cursor` class with `move_to(pos)`, `move_left(n)`, `move_right(n)` methods.
4. Add `type_at_cursor(text)` — inserts text at the current cursor position.
5. Add `select(start, end)` and `delete_selection()` for range-based editing.
6. Write tests for all fixed bugs and new features.

## What We Evaluate
- Data structure choice for efficient text operations
- Undo/redo pattern (command pattern or memento)
- Edge case handling
- Test coverage and quality
