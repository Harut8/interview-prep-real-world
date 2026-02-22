# Task 24: Design ATM Machine — Fix Bugs & Add Full Transaction Support

**Time limit: 60 minutes**

## Existing Codebase
An ATM machine simulator with account management, cash dispensing, and basic transaction support. Handles PIN verification and balance operations.

## Problems to Fix
1. The `withdraw` method doesn't check denomination availability — it approves withdrawals even when the ATM can't make change.
2. The `authenticate` method doesn't lock accounts after failed PIN attempts — allows brute force.
3. The `deposit` method adds to balance before validating the deposit amount — negative deposits increase balance.
4. The `get_balance` method exposes balance without checking if the session is authenticated.

## Features to Implement
1. Add denomination management — ATM tracks available bills ($100, $50, $20, $10, $5) and dispenses optimally.
2. Add `transfer(from_account, to_account, amount)` between accounts.
3. Add transaction history with `get_statement(account_id, n)` — returns last n transactions.
4. Add daily withdrawal limit per account (configurable, default $1000).
5. Add session management with auto-timeout after 30 seconds of inactivity.
6. Write tests for all fixed bugs and new features.

## What We Evaluate
- State machine design (session states)
- Greedy algorithm for cash dispensing
- Security considerations (PIN, limits, sessions)
- Transaction integrity
- Test coverage
