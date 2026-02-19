1. Session ID — cryptographically secure (line 21)
    - `random.randint(100000, 999999)` has only 900k values — trivially brutable
    - fix: `secrets.token_hex(32)` — 64 hex chars with cryptographic randomness
    - test expects `len(sid) >= 32`

2. Session TTL with sliding expiration
    - on create: set `expires_at = time.time() + ttl`
    - on EVERY access (`get_session`, `/me`): extend `expires_at = time.time() + ttl`
      (this is the "sliding" part — session stays alive as long as user is active)
    - on get: check if `time.time() > expires_at` → delete session, return None
    - store both `created_at` and `last_accessed_at` timestamps

3. Secondary index for `get_all_sessions_for_user` (line 51-56)
    - maintain `user_sessions: dict[str, set[str]]` — user_id → set of session_ids
    - update in `create_session` (add) and `delete_session` (remove)
    - makes lookup O(1) instead of O(n)
    - NOTE: must keep in sync — when session expires and is lazily deleted,
      also remove from secondary index

4. Deleted session returns 500 (line 83-85)
    - `session` is None but code accesses `session["username"]` → NoneType error
    - fix: check for None and return 401:
        ```
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        ```

5. `DELETE /sessions` — invalidate all sessions for current user
    ```
    @app.delete("/sessions")
    def delete_all_sessions(request: Request, response: Response):
        session_id = request.cookies.get("session_id")
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=401)
        user_id = session["user_id"]
        for sid in list(user_sessions.get(user_id, [])):
            delete_session(sid)
        response.delete_cookie("session_id")
    ```

6. Session metadata — store context from request
    - `create_session` needs the `Request` object to capture:
        - `user_agent`: `request.headers.get("user-agent")`
        - `ip_address`: `request.client.host`
        - `created_at`: `time.time()`
        - `last_accessed_at`: `time.time()` (updated on each access)

7. Cookie security flags (line 73) — missing critical flags
    - `httponly=True` — prevents JavaScript access (XSS protection)
    - `secure=True` — only send over HTTPS
    - `samesite="lax"` — CSRF protection
    ```
    response.set_cookie("session_id", session_id, httponly=True, secure=True, samesite="lax")
    ```

8. Password comparison not timing-safe (line 69)
    - `user["password"] != request.password` is vulnerable to timing attacks
    - fix: `secrets.compare_digest(user["password"], request.password)`
    - also: passwords stored in plain text — production should use bcrypt/argon2

9. Session cleanup / garbage collection
    - expired sessions accumulate in memory forever
    - need periodic cleanup (background task) or lazy deletion on access
    - lazy: check expiry in `get_session`, delete if expired
    - periodic: sweep all sessions, delete expired ones

10. Session ID collision (line 21)
    - current 6-digit numbers: collision very likely at scale
    - even with `secrets.token_hex(32)`, `create_session` doesn't check for existing ID
    - extremely unlikely with 64-char hex, but current code is dangerous

11. Tests to write
    - login returns session_id cookie with secure flags
    - deleted session returns 401 (not 500)
    - session ID is >= 32 chars, all unique across 1000 generations
    - session expires after TTL
    - sliding expiration: accessing session extends TTL
    - `DELETE /sessions` invalidates all sessions for user
    - other user's sessions unaffected by `DELETE /sessions`
    - session metadata: user agent and IP stored correctly
    - secondary index: `get_all_sessions_for_user` returns all sessions
    - expired session cleaned from secondary index
    - timing-safe: login doesn't leak password info via timing