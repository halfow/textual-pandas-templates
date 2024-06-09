# textual <3 pandas small examples

## Installation

```bash
pip install -e .[dev]
python examples/table.py --help
```

## Known issues and future work

- After new filter is applied sometimes the column with does not adjust correctly
- Filter invert would be a nice to have, would need to be applied as the last mask.
- As most filters act on `df.astype(str)` there might be benefits to cache this value.
