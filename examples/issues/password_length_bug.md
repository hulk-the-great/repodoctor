# Bug: password validator rejects passwords at the minimum length

`is_strong_password("abcde1gh")` has exactly 8 characters and a digit, so it should be accepted.
The function currently requires the length to be greater than the minimum instead of at least the minimum.
