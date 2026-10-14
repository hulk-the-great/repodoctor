# Bug: average returns the sum instead of the mean

The `average` function should divide the sum by the number of values.
`average([2, 4, 6])` should return `4`, not `12`.
