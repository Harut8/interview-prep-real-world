1. Price range — exclusive upper bound (line 93)
    - change `price <= ?` to `price < ?`
    - matches test expectation on line 54

2. AND/OR filter logic — AND is correct, need to ADD OR as option
    - current AND logic is correct for `category=electronics&min_price=10` (want both)
    - the bug is that there's no way to use OR at all
    - fix: add a `filter_logic` query parameter:
        ```
        filter_logic: str = Query("and", regex="^(and|or)$")
        where = "WHERE " + f" {filter_logic.upper()} ".join(conditions)
        ```

3. Window function for COUNT — eliminate separate query (lines 104-105)
    - `SELECT *, COUNT(*) OVER() as total FROM products`
    - returns total alongside each row, no extra query
    - edge case: empty result set → no rows returned, total is implicitly 0

4. Cursor-based pagination duplicates — the actual README bug
    - README says cursor-based pagination returns duplicates when items inserted between pages
    - current code uses offset-based (line 108), which has same problem: items shift on insert
    - fix: implement cursor-based pagination using `WHERE id > last_seen_id LIMIT ?`
    - client passes `?cursor=42` (last id seen), server returns items with `id > 42`
    - immune to inserts/deletes between pages
    - offset formula `(page - 1) * page_size` and `has_next` logic are already correct as-is

5. Multi-field sorting — needs SQL injection protection
    - parse `?sort=price:asc,name:desc` into field/direction pairs
    - validate against allowlist — NEVER interpolate raw user input into SQL:
        ```
        ALLOWED_SORT_FIELDS = {"id", "name", "category", "price", "in_stock"}
        ALLOWED_DIRECTIONS = {"asc", "desc"}
        ```
    - reject any field/direction not in allowlist (return 400)
    - build `ORDER BY price ASC, name DESC` from validated values

6. Sparse fieldsets — validate field names against allowlist
    - parse `?fields=id,name,price` into list
    - validate each field against `ALLOWED_FIELDS = {"id", "name", "category", "price", "in_stock"}`
    - reject unknown fields (return 400)
    - build `SELECT id, name, price FROM products` from validated values
    - same SQL injection risk as sorting — never use raw input

7. `category` filter truthiness bug (line 85)
    - `if category:` is falsy for empty string `""`
    - `?category=` won't apply the filter
    - fix: `if category is not None:`

8. f-string SQL construction (lines 104, 109)
    - `f"SELECT ... {where}"` is safe because `where` uses parameterized `?` placeholders
    - but f-strings for SQL are a code smell — easy to introduce injection if patterns change

9. Tests to write
    - price range: exclusive upper bound (item at exact max_price excluded)
    - AND filter: category + price range returns correct intersection
    - OR filter: category OR price range returns correct union
    - pagination: page 1 and page 2 return different items, no overlap
    - cursor pagination: inserting item between page fetches doesn't cause duplicates
    - sorting: `?sort=price:asc` returns items in ascending price order
    - sorting: multi-field `?sort=category:asc,price:desc` sorts correctly
    - sorting: invalid field name returns 400
    - sparse fieldsets: `?fields=id,name` returns only those fields
    - sparse fieldsets: invalid field name returns 400
    - SQL injection: sort/fields params with malicious input are rejected
    - empty category filter: `?category=` handled correctly
    - empty result set: returns `total=0`, empty items, `has_next=false`
