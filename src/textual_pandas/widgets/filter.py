import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, reduce
from itertools import chain
from types import MappingProxyType

from pandas import DataFrame, Series
from textual import on
from textual.containers import HorizontalScroll
from textual.message import Message
from textual.widgets import Input, SelectionList


class PandasFilterContainer(HorizontalScroll):
    """Container to manage filters for a DataFrame."""

    @dataclass
    class _Filter(Message):
        identity: int
        selection: Callable[[DataFrame], Series | DataFrame]

    class ColumnFilter(_Filter):
        selection: Callable[[DataFrame], Series]

    class IndexFilter(_Filter):
        selection: Callable[[DataFrame], Series]

    class CellFilter(_Filter):
        selection: Callable[[DataFrame], DataFrame]

    @dataclass
    class FilterChanged(Message):
        df: DataFrame

    def _update(self):
        index: Series["bool"] = self._index.all(axis=1)  # noqa: UP037
        _columns: Series["bool"] = self._column.all(axis=1)  # noqa: UP037
        columns: list[str] = _columns[_columns].index.to_list()
        cell = reduce(
            lambda x, y: x & (y[columns].any(axis=1) | y[columns].isna().all(axis=1)),
            self._cell.values(),
            Series(True, index=self.df.index),
        )
        self.post_message(self.FilterChanged(self.df[columns][cell & index]))

    @cached_property
    def _lookup(self):
        lookup = {
            self.CellFilter: self._cell,
            self.IndexFilter: self._index,
            self.ColumnFilter: self._column,
        }
        return MappingProxyType(lookup)

    async def update(self, df: DataFrame):
        self.df = df.astype(str)
        self._cell: dict[int, DataFrame] = {}
        self._index = DataFrame(index=df.index)
        self._column = DataFrame(index=df.columns)

        children = (c for c in self.children if hasattr(c, "apply_filter"))
        filters = chain.from_iterable(c.apply_filter() for c in children)  # type: ignore
        for message, identity, mask in filters:
            self._lookup[message][identity] = mask(self.df)
        self._update()

    @on(CellFilter)
    @on(IndexFilter)
    @on(ColumnFilter)
    async def _filter(self, event: _Filter):
        event.stop()
        self._lookup[type(event)][event.identity] = event.selection(self.df)  # type: ignore
        self._update()


class PandasIndexInputFilter(Input):
    def mask(self, df: DataFrame) -> Series:
        try:
            re.compile(self.value, re.IGNORECASE)
        except re.error:
            return Series(False, index=df.index, dtype="boolean")
        return df.index.astype(str).str.contains(self.value, case=False, regex=True)

    def apply_filter(self):
        yield PandasFilterContainer.IndexFilter, id(self), self.mask

    def _watch_value(self, value: str) -> None:
        for message, identity, func in self.apply_filter():
            self.post_message(message(identity, func))


class PandasCellSearch(Input):
    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = columns

    def mask(self, df: DataFrame):
        _df = DataFrame(index=df.index, columns=df.columns, dtype="boolean")
        try:
            re.compile(self.value, re.IGNORECASE)
        except re.error:
            return _df

        columns = self.columns or df.columns
        _df[columns] = df[columns].apply(lambda x: x.str.contains(self.value, case=False, regex=True))
        return _df

    def apply_filter(self):
        yield PandasFilterContainer.CellFilter, id(self), self.mask

    def _watch_value(self, value: str) -> None:
        for message, identity, func in self.apply_filter():
            self.post_message(message(identity, func))


class PandasColumnSelectFilter(SelectionList):
    def mask(self, df: DataFrame) -> Series:
        series = Series(False, index=df.columns, dtype="boolean")
        if self.selected:
            series[self.selected] = True
        return series

    def apply_filter(self):
        yield PandasFilterContainer.ColumnFilter, id(self), self.mask

    def _message_changed(self) -> None:
        if self._send_messages:
            for message, identity, func in self.apply_filter():
                self.post_message(message(identity, func))


class PandasCellSelectFilter(SelectionList):
    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = columns

    def mask(self, df: DataFrame) -> DataFrame:
        mask = DataFrame(index=df.index, columns=df.columns, dtype="boolean")
        columns = self.columns or df.columns
        mask[columns] = df[columns].isin(self.selected) if self.selected else False
        return mask

    def apply_filter(self):
        yield PandasFilterContainer.CellFilter, id(self), self.mask

    def _message_changed(self) -> None:
        if self._send_messages:
            for message, identity, func in self.apply_filter():
                self.post_message(message(identity, func))
