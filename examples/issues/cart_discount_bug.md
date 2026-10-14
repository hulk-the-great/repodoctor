# Bug: discount calculation returns only the discount amount

`apply_discount(total, discount_percent)` should return the price after discount.
For example, `apply_discount(100, 20)` should return `80`, not `20`.
