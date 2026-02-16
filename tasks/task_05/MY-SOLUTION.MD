1. Pagination bug:
    - lets say limit per page is 10
    - it means for page 1 we show from 1 to 10
    - for page 2 we show from 11 to 20
    - so if we have 20 items we show 2 pages
    - but if we have 21 items we show 3 pages
    - then offset should be
        - page 1: 0
        - page 2: 10
        - page 3: 20
    - it means offset formula (page - 1) * limit
2. Update book bug:
    - actualy not so bugly since postgres doesnt throw error on update/delete if id doesnt exist
    - but we can do pre-check if book exists and throw 404 if not + update if exists
    - cursor.rowcount after the UPDATE — if it's 0,
      the row didn't exist. One query instead of two.
3. For search we can use different approaches
    - by title using simple ILIKE check
    - by author using simple ILIKE check
    - by genre using simple ILIKE check
    - by year using simple ILIKE check
    - or we can combine into one query using bm25 index
    - or can have post compute fields from existing fields and use them for search
4. Stats can be computed using
    - simple count(*)
    - or can have post compute fields from existing fields and store them in separate table
    - or can use materialized views