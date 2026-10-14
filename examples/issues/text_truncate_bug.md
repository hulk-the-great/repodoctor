# Bug: truncate returns strings longer than the requested maximum length

`truncate("abcdefghij", 7)` should return `"abcd..."` with total length 7.
The current function appends the ellipsis after taking `max_length` characters.
