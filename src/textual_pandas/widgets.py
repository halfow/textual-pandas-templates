import pandas as pd
from textual import on
from textual.containers import Container
from textual.widgets import DataTable as _DataTable
from textual.widgets import Input


class DataTable(_DataTable):
    async def update(self, data: pd.DataFrame, index: str = "Index", height: int | None = 1):
        self.clear(columns=True)
        self.add_columns(index, *data.columns)
        for row in data.itertuples():
            self.add_row(*row, height=height)


class SortableDataTable(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sorted_by = None

    @on(_DataTable.HeaderSelected)
    async def _sort(self, event: _DataTable.HeaderSelected):
        column = event.column_key
        self._sorted_by = None if self._sorted_by == column else column
        self.sort(column, reverse=self._sorted_by is None)


class TextFilterDataTable(Container):
    def compose(self):
        yield Input(placeholder="Filter")
        yield SortableDataTable()

    async def update(self, df: pd.DataFrame, index: str = "Index", height: int | None = 1):
        self.df, self.index, self.height = df, index, height
        await self.query_one(SortableDataTable).update(df, index, height)

    @on(Input.Changed)
    async def _filter(self, event: Input.Changed):
        df = self.df
        if event.value:
            imask = df.index.astype(str).str.contains(event.value, case=False)
            rmask = df.astype(str).apply(lambda x: x.str.contains(event.value, case=False).any(), axis=1)
            df = df[rmask | imask]
        await self.query_one(SortableDataTable).update(df, self.index, self.height)
