from natsort import natsort_keygen
from pandas import DataFrame
from textual import on
from textual.widgets import DataTable as _DataTable


class DataTable(_DataTable):
    async def update(self, data: DataFrame, index: str | None = None, height: int | None = 1):
        self.clear(columns=True)
        if index:
            self.add_column(index)
        self.add_columns(*data.columns)
        for row in data.itertuples(index=bool(index)):
            self.add_row(*row, height=height)


class SortableDataTable(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sorted_by = None

    @on(_DataTable.HeaderSelected)
    async def _sort(self, event: _DataTable.HeaderSelected):
        column = event.column_key
        self._sorted_by = None if self._sorted_by == column else column
        self.sort(column, reverse=self._sorted_by is None, key=natsort_keygen())
