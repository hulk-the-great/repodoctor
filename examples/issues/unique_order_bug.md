# Bug: unique list helper sorts items instead of preserving order

`unique_preserve_order(["b", "a", "b", "c", "a"])` should return `["b", "a", "c"]`.
The function should keep the first occurrence order.
