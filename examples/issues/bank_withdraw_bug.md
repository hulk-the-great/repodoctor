# Bug: withdrawing the full balance is incorrectly rejected

An account with balance 50 should allow withdrawing 50 and leave balance 0.
The overdraft check should reject negative balances, not zero balances.
