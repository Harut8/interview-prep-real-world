# Task 02: User Authentication Service — Fix Security Issues & Add Token Refresh

**Time limit: 60 minutes**

## Existing Codebase
A simple user registration/login service using Flask. Users can register, login, and access protected routes.

## Problems to Fix
1. Passwords are stored in plain text — fix to use proper hashing.
2. The `login` endpoint is vulnerable to timing attacks when comparing passwords.
3. The JWT token never expires — add expiration.
4. SQL injection vulnerability in the `get_user_by_username` function.

## Features to Implement
1. Add a `POST /refresh` endpoint that accepts an expired (but valid) token and returns a new one.
2. Write comprehensive pytest tests.

## What We Evaluate
- Security awareness
- Proper password hashing (bcrypt/argon2)
- JWT handling
- Test quality
