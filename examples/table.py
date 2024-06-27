from pathlib import Path

from natsort import natsorted
from pandas import DataFrame, read_csv
from textual.app import App
from textual.containers import Container
from textual_pandas.widgets import (
    DataTable,
    PandasCellSearch,
    PandasCellSelectFilter,
    PandasColumnSelectFilter,
    PandasContainer,
    PandasIndexInputFilter,
    SortableDataTable,
)


class ExampleApp(App):
    CSS_PATH = "table.tcss"

    def __init__(self, path: Path):
        self.path = path
        self.df: DataFrame = read_csv(path)
        super().__init__()


class ExampleBasic(ExampleApp):
    def compose(self):
        yield DataTable()

    async def on_mount(self):
        frame = self.query_one(DataTable)
        await frame.update(self.df)  # type: ignore


class ExampleSortable(ExampleApp):
    def compose(self):
        yield SortableDataTable()

    async def on_mount(self):
        frame = self.query_one(SortableDataTable)
        frame.border_title = str(self.path)
        await frame.update(self.df)  # type: ignore


class ExampleFilter(ExampleApp):
    def compose(self):
        self.table = PandasContainer()
        yield self.table

    async def on_mount(self):
        self.query_one(SortableDataTable).border_title = str(self.path)
        await self.table.update(self.df)
        await self.table.add_filter(PandasIndexInputFilter(placeholder="Filter"))
        for column in self.df.columns:
            values = self.df[column].unique().astype(str)
            cf = PandasCellSelectFilter(*((c, c, True) for c in values), columns=[column])
            cf.border_title = column
            await self.table.add_filter(cf)


class ExampleColumnSelect(ExampleApp):
    def compose(self):
        self.table = PandasContainer()
        yield self.table

    async def on_mount(self):
        self.query_one(SortableDataTable).border_title = str(self.path)
        await self.table.update(self.df, index="Index")

        select = PandasColumnSelectFilter(*((c, c, True) for c in self.df.columns), classes="filter")
        select.border_title = "Columns"

        index = PandasIndexInputFilter(placeholder="Filter", classes="filter")
        index.border_title = "Index Filter"

        cell = PandasCellSearch(placeholder="Non-index regex", classes="filter")
        cell.border_title = "Cell Filter"

        await self.table.add_filter(Container(index, select, classes="filter-box"), cell)

        for column in self.df.columns:
            values = natsorted(self.df[column].unique().astype(str))
            cf = PandasCellSelectFilter(*((c, c, True) for c in values), columns=[column], classes="filter")
            cf.border_title = column
            await self.table.add_filter(cf)


if __name__ == "__main__":
    from argparse import ArgumentParser

    widgets = {
        "basic": ExampleBasic,
        "sort": ExampleSortable,
        "filter": ExampleFilter,  # TODO: Will not work properly with custom data, as selection is hardcoded
        "column": ExampleColumnSelect,
    }
    parser = ArgumentParser()
    parser.add_argument(
        "widget",
        choices=widgets.keys(),
    )
    parser.add_argument(
        *("-p", "--path"),
        default=Path(__file__).with_name("data.csv"),
        type=Path,
    )
    args = parser.parse_args()
    app = widgets[args.widget](args.path).run()
