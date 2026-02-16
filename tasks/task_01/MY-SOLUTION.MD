1. URL parsing bug
    - use urlparse from urllib.parse
    - check if url is valid (scheme and netloc exist raise 422)
    - check if url is empty (raise 422)
    - check if url is not a url (raise 422)
2. When url get executed
    - get from storate dict
    - check if url is exists
    - if not exists return 404
    - if exists increment click_count
    - return RedirectResponse to original_url
3. Delete url
    - get from storate dict
    - check if url is exists (optional)
    - if not exists return 404 (optional)
    - if exists delete from storage
    - return True
    - add endpoint for delete url
4. Add GET /stats/{short_id} endpoint
    - get from storate dict
    - check if url is exists
    - if not exists return 404
    - if exists return JSON with original_url, created_at, click_count
5. Write pytest tests for all fixed bugs and the new endpoint
    - test url parsing bug
    - test when url get executed
    - test delete url
    - test GET /stats/{short_id} endpoint