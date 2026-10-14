# Bug: file extension helper returns the name prefix

`get_extension("report.pdf")` should return `"pdf"`, and `get_extension("archive.tar.gz")` should return `"gz"`.
The helper currently returns the part before the first dot.
