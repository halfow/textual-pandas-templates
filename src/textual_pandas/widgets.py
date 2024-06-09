from collections.abc import Callable
from functools import reduce
from typing import Union

import pandas as pd
from pandas import DataFrame, Series
from textual import on
from textual.containers import Container, HorizontalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable as _DataTable
from textual.widgets import Input, SelectionList


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


class PandasContainer(Container):
    class Mask(Message):
        def __init__(self, identity: int, mask: Callable[[DataFrame], Union["Series[bool]", None]]) -> None:
            super().__init__()
            self.identity = identity
            self.mask = mask

    def compose(self):  # TODO: Support custom visualizations instead of just table
        yield HorizontalScroll()
        yield SortableDataTable()

    async def add_filter(self, *widget: Widget):
        await self.get_child_by_type(HorizontalScroll).mount(*widget)

    async def update(self, df: DataFrame, index="Index", height=1):
        self.df, self.index, self.height = df, index, height
        self.masks: dict[int, "Series[bool]"] = {}  # noqa: UP037
        await self.query_one(SortableDataTable).update(df, index, height)

    @on(Mask)
    async def _filter(self, event: Mask):
        """Filter the DataFrame based on the provided masks."""
        event.stop()
        if self.df.empty:
            return

        mask = event.mask(self.df)
        if mask is None:
            self.masks.pop(event.identity, None)
        else:
            self.masks[event.identity] = mask

        if self.masks:
            df = self.df[reduce(lambda x, y: x & y, self.masks.values())]
        else:
            df = self.df

        await self.query_one(SortableDataTable).update(df, self.index, self.height)


class PandasInputFilter(Input):
    def _watch_value(self, value: str) -> None:
        self._suggestion = ""
        if self.suggester and value:
            self.run_worker(self.suggester._get_suggestion(self, value))
        if self.styles.auto_dimensions:
            self.refresh(layout=True)

        def mask(df: DataFrame) -> Union["Series[bool]", None]:  # TODO: allow mask to be created for specific columns
            if not value:
                return None
            index = df.index.astype(str).str.contains(value, case=False)
            row = df.astype(str).apply(lambda x: x.str.contains(value, case=False).any(), axis=1)
            return index.__or__(row)

        self.post_message(PandasContainer.Mask(id(self), mask))


class PandasSelectFilter(SelectionList):
    def _message_changed(self) -> None:
        if not self._send_messages:
            return
        self.post_message(PandasContainer.Mask(id(self), lambda df: df.astype(str).isin(self.selected).any(axis=1)))
