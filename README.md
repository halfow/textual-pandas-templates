# textual <3 pandas small examples

## Installation

```bash
pip install -e .[dev]
python examples/table.py --help
```

## Known issues and future work

- After new filter is applied sometimes the column with does not adjust correctly
- Allow filters to only act on specific columns."selection narrowing"
  - Not a big thing the reader should be able to do the adaptations needed for their case.
  - A general solution would be nice
- How to handle filters if the overlying df gets updated?
- Filter invert would be a nice to have, would need to be applied as the last mask.
- Data table column selection would be nice to have. Would require a wrapper layer, would require all filters to be recalculated. Thus require keep or fetch for all mask functions, to rerun in the new context.
- As most filters act on `df.astype(str)` there might be benefits to cache this value.
