# Bug: slugify uses the wrong separator

The `slugify` helper should create URL slugs with hyphens, not underscores.
Example: `slugify("Hello World")` should return `hello-world`.
