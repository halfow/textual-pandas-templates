from textual.app import App
from textual_pandas.widgets import DataTable, PandasContainer, PandasInputFilter, PandasSelectFilter, SortableDataTable


class ExampleApp(App):
    def __init__(self, df):
        self.df = df
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
        await frame.update(self.df)  # type: ignore


class ExampleFilter(ExampleApp):
    DEFAULT_CSS = """
        PandasContainer > HorizontalScroll {
            height: 5;
        }
        PandasContainer > HorizontalScroll > * {
            width: 20;
        }
    """

    def compose(self):
        self.table = PandasContainer()
        yield self.table

    async def on_mount(self):
        await self.table.update(self.df)
        await self.table.add_filter(PandasInputFilter(placeholder="Filter"))
        await self.table.add_filter(PandasInputFilter(placeholder="Another filter"))
        await self.table.add_filter(PandasSelectFilter(("Male", "Male", True), ("Female", "Female", True)))


if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path

    from pandas import read_csv

    widgets = {
        "basic": ExampleBasic,
        "sort": ExampleSortable,
        "filter": ExampleFilter,  # TODO: Will not work properly with custom data, as selection is hardcoded
    }
    parser = ArgumentParser()
    parser.add_argument("widget", choices=widgets.keys())
    parser.add_argument("-p", "--path", default=Path(__file__).with_name("data.csv"), type=Path)
    args = parser.parse_args()

    widgets[args.widget](read_csv(args.path)).run()
