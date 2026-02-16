# Task 18: Middleware Pipeline — Fix Ordering & Add Logging/Auth Middleware

**Time limit: 60 minutes**

## Existing Codebase
A middleware pipeline system for processing HTTP-like requests. Each middleware can modify the request, call the next middleware, and modify the response.

## Problems to Fix
1. Middleware execution order is reversed — last added runs first instead of first added.
2. If a middleware raises an exception, the response middleware chain is not executed (no cleanup).
3. The `MiddlewareChain.add()` method doesn't validate that middleware implements the correct interface.
4. Context object is mutable and shared — one middleware can corrupt state for others.

## Features to Implement
1. Add `TimingMiddleware` that measures request processing time and adds it to response headers.
2. Add `AuthMiddleware` that checks for an API key in headers and returns 401 if missing/invalid.
3. Add `LoggingMiddleware` that logs request method, path, status code, and timing.
4. Write tests for the middleware chain and each middleware.

## What We Evaluate
- Chain of responsibility pattern
- Error handling in pipelines
- Immutability / defensive copying
- Middleware design
