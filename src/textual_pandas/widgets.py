import re
from collections.abc import Callable
from functools import cached_property, reduce
from types import MappingProxyType

import pandas as pd
from natsort import natsort_keygen
from pandas import DataFrame, Series
from textual import on
from textual.containers import Container, HorizontalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable as _DataTable
from textual.widgets import Input, SelectionList


class DataTable(_DataTable):
    async def update(self, data: pd.DataFrame, index: str | None = None, height: int | None = 1):
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


class PandasContainer(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filters
        self._cell: dict[int, "DataFrame[bool]"]  # type: ignore # noqa: UP037
        self._index: "DataFrame[bool]"  # type: ignore # noqa: UP037
        self._column: "DataFrame[bool]"  # type: ignore # noqa: UP037

    class _Filter(Message):
        def __init__(self, identity: int, selection):
            super().__init__()
            self.identity = identity
            self.selection = selection

    class ColumnFilter(_Filter):
        selection: Callable[[DataFrame], "Series[bool]"]

    class IndexFilter(_Filter):
        selection: Callable[[DataFrame], "Series[bool]"]

    class CellFilter(_Filter):
        selection: Callable[[DataFrame], "DataFrame[bool]"]

    def compose(self):  # TODO: Support custom visualizations instead of just table
        yield HorizontalScroll(classes="filter-container")
        yield SortableDataTable(classes="table")

    async def add_filter(self, *widget: Widget):
        await self.get_child_by_type(HorizontalScroll).mount(*widget)

    async def _update(self):
        _col = self._column.all(axis=1)
        col = _col[_col].index.to_list()
        index = self._index.all(axis=1)
        cell = reduce(
            lambda x, y: x & (y[col].any(axis=1) | y[col].isna().all(axis=1)),
            self._cell.values(),
            Series(True, index=self.df.index),
        )
        await self.query_one(SortableDataTable).update(self.df[col][cell & index], self.index, self.height)

    @cached_property
    def _lookup(self):
        lookup = {
            self.CellFilter: self._cell,
            self.IndexFilter: self._index,
            self.ColumnFilter: self._column,
        }
        return MappingProxyType(lookup)

    async def update(self, df: DataFrame, index=None, height=1):
        self.df, self.index, self.height = df.astype(str), index, height
        self._cell = {}
        self._index = DataFrame(index=df.index)
        self._column = DataFrame(index=df.columns)

        _children = (c for c in self.get_child_by_type(HorizontalScroll).children if hasattr(c, "apply_filter"))
        _filters = (c.apply_filter() for c in _children)  # type: ignore
        for message, identity, mask in _filters:
            self._lookup[message][identity] = mask(self.df)

        await self._update()

    @on(CellFilter)
    @on(IndexFilter)
    @on(ColumnFilter)
    async def _filter(self, event: _Filter):
        event.stop()
        self._lookup[type(event)][event.identity] = event.selection(self.df)  # type: ignore
        await self._update()


class PandasIndexInputFilter(Input):
    def mask(self, df: DataFrame) -> "Series[bool]":
        if self.value:
            return df.index.astype(str).str.contains(self.value, case=False)
        return Series(True, index=df.index)

    def apply_filter(self):
        yield PandasContainer.IndexFilter, id(self), self.mask

    def _watch_value(self, value: str) -> None:
        for filter, identity, func in self.apply_filter():
            self.post_message(filter(identity, func))


class PandasCellSearch(Input):
    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.regex = re.compile(self.value, re.IGNORECASE)
        self.columns = columns

    def mask(self, df: DataFrame):
        search = lambda x: bool(self.regex.search(str(x)))  # noqa: E731
        _df = df.map(lambda _: pd.NA)
        if self.value:
            columns = self.columns or df.columns
            _df[columns] = df[columns].map(search)
        return _df

    def apply_filter(self):
        yield PandasContainer.CellFilter, id(self), self.mask

    def _watch_value(self, value: str) -> None:
        try:
            self.regex = re.compile(self.value, re.IGNORECASE)
        except re.error:
            return

        for filter, identity, func in self.apply_filter():
            self.post_message(filter(identity, func))


class PandasColumnSelectFilter(SelectionList):
    def mask(self, df: DataFrame) -> "Series[bool]":
        series = Series(False, index=df.columns)
        if self.selected:
            series[self.selected] = True
        return series

    def apply_filter(self):
        yield PandasContainer.ColumnFilter, id(self), self.mask

    def _message_changed(self) -> None:
        if self._send_messages:
            for filter, identity, func in self.apply_filter():
                self.post_message(filter(identity, func))


class PandasCellSelectFilter(SelectionList):
    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = columns

    def mask(self, df: DataFrame) -> "DataFrame[bool]":
        _mask = df.map(lambda _: pd.NA)
        _col = self.columns or df.columns
        _mask[_col] = df[_col].isin(self.selected) if self.selected else False
        return _mask

    def apply_filter(self):
        yield PandasContainer.CellFilter, id(self), self.mask

    def _message_changed(self) -> None:
        if self._send_messages:
            for filter, identity, func in self.apply_filter():
                self.post_message(filter(identity, func))
