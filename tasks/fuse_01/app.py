class CircularDependencyError(Exception):
    pass


class Spreadsheet:
    """Cells hold either a literal number or a formula.

    State is split so that undo can restore a single cell exactly:
      values     — literal value per cell
      formulas   — formula source per cell (mutually exclusive with values)
      deps       — cell -> cells it reads (precedents)
      dependents — cell -> cells that read it (reverse edges, for invalidation)
      cache      — memoised formula results, dropped along the dependency chain
    """

    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self.values: dict[str, int | float] = {}
        self.formulas: dict[str, str] = {}
        self.deps: dict[str, set[str]] = {}
        self.dependents: dict[str, set[str]] = {}
        self.cache: dict[str, int | float] = {}
        self.history: list[tuple[str, int | float | None, str | None, set[str]]] = []

    # --- cell addressing -------------------------------------------------

    def _parse_cell(self, cell: str) -> tuple[int, int]:
        """"B3" -> (col=2, row=3). Raises on malformed or out-of-range refs."""
        i = 0
        while i < len(cell) and cell[i].isalpha():
            i += 1
        if i == 0 or i == len(cell) or not cell[i:].isdigit():
            raise ValueError(f"Malformed cell reference: {cell!r}")
        col = 0
        for ch in cell[:i]:
            col = col * 26 + (ord(ch.upper()) - ord("A") + 1)
        row = int(cell[i:])
        if not (1 <= row <= self.rows) or not (1 <= col <= self.cols):
            raise ValueError(f"Cell out of range: {cell!r}")
        return col, row

    def _cell_name(self, col: int, row: int) -> str:
        letters = ""
        while col > 0:
            col, rem = divmod(col - 1, 26)
            letters = chr(ord("A") + rem) + letters
        return f"{letters}{row}"

    def _expand_range(self, ref: str) -> list[str]:
        """"A1:B2" -> [A1, A2, B1, B2]."""
        start, _, end = ref.partition(":")
        start_col, start_row = self._parse_cell(start)
        end_col, end_row = self._parse_cell(end)
        cells = []
        for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
            for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
                cells.append(self._cell_name(col, row))
        return cells

    # --- formula parsing -------------------------------------------------

    def _tokenize(self, expr: str) -> list[str]:
        """Split an expression into cell refs, numbers and operators."""
        expr = expr.replace(" ", "")
        tokens = []
        i = 0
        while i < len(expr):
            ch = expr[i]
            if ch in "+-*":
                tokens.append(ch)
                i += 1
            elif ch.isalpha():
                j = i
                while j < len(expr) and expr[j].isalpha():
                    j += 1
                while j < len(expr) and expr[j].isdigit():
                    j += 1
                tokens.append(expr[i:j])
                i = j
            elif ch.isdigit():
                j = i
                while j < len(expr) and (expr[j].isdigit() or expr[j] == "."):
                    j += 1
                tokens.append(expr[i:j])
                i = j
            else:
                raise ValueError(f"Unexpected character {ch!r} in formula")
        if not tokens or len(tokens) % 2 == 0:
            raise ValueError(f"Malformed formula: {expr!r}")
        return tokens

    def _is_cell_ref(self, token: str) -> bool:
        return token[0].isalpha()

    def _formula_deps(self, formula: str) -> set[str]:
        """Cells a formula reads, without evaluating it."""
        body = formula[1:]
        if body.upper().startswith("SUM(") and body.endswith(")"):
            return set(self._expand_range(body[4:-1]))
        deps = set()
        for token in self._tokenize(body):
            if token not in "+-*" and self._is_cell_ref(token):
                self._parse_cell(token)  # validate
                deps.add(token)
        return deps

    def _evaluate(self, formula: str) -> int | float:
        body = formula[1:]
        if body.upper().startswith("SUM(") and body.endswith(")"):
            return sum(self.get(c) for c in self._expand_range(body[4:-1]))

        tokens = self._tokenize(body)

        def operand(token: str) -> int | float:
            if self._is_cell_ref(token):
                return self.get(token)
            return float(token) if "." in token else int(token)

        # Fold '*' eagerly, defer '+'/'-' — gives normal precedence in one pass.
        terms = [operand(tokens[0])]
        ops = []
        for i in range(1, len(tokens), 2):
            op, value = tokens[i], operand(tokens[i + 1])
            if op == "*":
                terms[-1] *= value
            else:
                ops.append(op)
                terms.append(value)

        result = terms[0]
        for i, op in enumerate(ops):
            result = result + terms[i + 1] if op == "+" else result - terms[i + 1]
        return result

    # --- graph maintenance -----------------------------------------------

    def _would_cycle(self, cell: str, new_deps: set[str]) -> bool:
        """Would `cell` reading `new_deps` close a loop back onto `cell`?"""
        stack = list(new_deps)
        seen = set()
        while stack:
            current = stack.pop()
            if current == cell:
                return True
            if current in seen:
                continue
            seen.add(current)
            stack.extend(self.deps.get(current, ()))
        return False

    def _invalidate(self, cell: str) -> None:
        """Drop cached results for `cell` and everything downstream of it."""
        stack = [cell]
        seen = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            self.cache.pop(current, None)
            stack.extend(self.dependents.get(current, ()))

    def _write(
        self,
        cell: str,
        value: int | float | None,
        formula: str | None,
        deps: set[str],
    ) -> None:
        """Overwrite one cell's value, formula and edges. Assumes no cycle."""
        for old in self.deps.get(cell, set()):
            self.dependents.get(old, set()).discard(cell)
        self.deps[cell] = set(deps)
        for new in deps:
            self.dependents.setdefault(new, set()).add(cell)

        if formula is None:
            self.formulas.pop(cell, None)
        else:
            self.formulas[cell] = formula
        if value is None:
            self.values.pop(cell, None)
        else:
            self.values[cell] = value

        self._invalidate(cell)

    def _snapshot(self, cell: str) -> tuple[str, int | float | None, str | None, set[str]]:
        return (
            cell,
            self.values.get(cell),
            self.formulas.get(cell),
            set(self.deps.get(cell, set())),
        )

    # --- public API ------------------------------------------------------

    def set(self, cell: str, value) -> None:
        self._parse_cell(cell)

        if isinstance(value, str):
            if not value.startswith("="):
                raise ValueError(f"String values must be formulas starting with '=': {value!r}")
            deps = self._formula_deps(value)
            # Check before touching state so a rejected set leaves the sheet intact.
            if self._would_cycle(cell, deps):
                raise CircularDependencyError(f"{cell} would depend on itself")
            snapshot = self._snapshot(cell)
            self._write(cell, None, value, deps)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            snapshot = self._snapshot(cell)
            self._write(cell, value, None, set())
        else:
            raise ValueError(f"Unsupported cell value: {value!r}")

        self.history.append(snapshot)

    def get(self, cell: str) -> int | float:
        self._parse_cell(cell)
        if cell in self.formulas:
            if cell not in self.cache:
                self.cache[cell] = self._evaluate(self.formulas[cell])
            return self.cache[cell]
        return self.values.get(cell, 0)

    def undo(self) -> None:
        if not self.history:
            return
        cell, value, formula, deps = self.history.pop()
        self._write(cell, value, formula, deps)
