# Bug: leap-year logic rejects years divisible by 400

In the Gregorian calendar, years divisible by 400 are leap years.
`is_leap_year(2000)` should return True, while `is_leap_year(1900)` should return False.
