from pathlib import Path

from natsort import natsorted
from pandas import DataFrame, read_csv
from textual import on
from textual.app import App
from textual.containers import Container, Horizontal
from textual.widgets import Pretty
from textual_pandas.widgets.filter import (
    PandasCellSearch,
    PandasCellSelectFilter,
    PandasColumnSelectFilter,
    PandasFilterContainer,
    PandasIndexInputFilter,
)
from textual_pandas.widgets.table import SortableDataTable


class PandasSummary(Container):
    """Example to show that the df can be consumed by other widgets."""

    def compose(self):
        self.pretty = Pretty("")
        self.border_title = "Summary of current selection"
        yield self.pretty

    async def update(self, df: DataFrame):
        self.pretty.update("No data" if df.empty else df.describe())


class TableFilterApp(App):
    CSS_PATH = "table.tcss"

    def __init__(self, path: Path):
        self.path = path
        self.df: DataFrame = read_csv(path)
        super().__init__()

    def compose(self):
        self.table = SortableDataTable(classes="table")
        self.filter = PandasFilterContainer(classes="container")

        self.table.border_title = str(self.path)
        self.filter.border_title = "Filters"
        yield self.filter
        with Horizontal():
            yield self.table
            yield PandasSummary(classes="container")

    async def on_mount(self):
        cell = PandasCellSearch(placeholder="Regex", classes="filter")
        index = PandasIndexInputFilter(placeholder="Regex", classes="filter")
        select = PandasColumnSelectFilter(*((c, c, True) for c in self.df.columns), classes="filter")

        cell.border_title = "Cell Filter"
        index.border_title = "Index Filter"
        select.border_title = "Columns"

        await self.filter.mount(Container(index, select), cell)

        for column in self.df.columns:
            values = natsorted(self.df[column].unique().astype(str))
            cf = PandasCellSelectFilter(*((c, c, True) for c in values), columns=[column], classes="filter")
            cf.border_title = column
            await self.filter.mount(cf)
        await self.filter.update(self.df)

    @on(PandasFilterContainer.FilterChanged)
    async def update(self, event: PandasFilterContainer.FilterChanged):
        """Recreate the table with new data."""
        event.stop()
        await self.table.update(event.df, index="Index")
        await self.query_one(PandasSummary).update(event.df)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        *("-p", "--path"),
        default=Path(__file__).with_name("data.csv"),
        type=Path,
    )
    args = parser.parse_args()
    app = TableFilterApp(args.path).run()
