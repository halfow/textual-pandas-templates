from pathlib import Path

from pandas import DataFrame, read_csv
from textual import on
from textual.app import App
from textual.widgets import SelectionList
from textual_pandas.widgets import DataTable, PandasContainer, PandasInputFilter, PandasSelectFilter, SortableDataTable


class ExampleApp(App):
    DEFAULT_CSS = """
        PandasContainer > HorizontalScroll {
            height: 5;
        }
        PandasContainer > HorizontalScroll > * {
            width: 20;
        }
        #cs:focus,
        PandasContainer > HorizontalScroll > *:focus {
            border: round deepskyblue;
        }
        #cs,
        SortableDataTable,
        PandasContainer > HorizontalScroll > * {
            border: round orange;
        }
    """

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
        await self.table.add_filter(PandasInputFilter(placeholder="Filter"))
        await self.table.add_filter(PandasInputFilter(placeholder="Another filter"))
        for column in self.df.columns:
            values = self.df[column].unique().astype(str)
            cf = PandasSelectFilter(*((c, c, True) for c in values), columns=[column])
            cf.border_title = column
            await self.table.add_filter(cf)


class ExampleColumnSelect(ExampleApp):
    def compose(self):
        self.table = PandasContainer()
        select = SelectionList(*((c, c, True) for c in self.df.columns), id="cs")
        select.border_title = "Columns"
        yield select
        yield self.table

    async def on_mount(self):
        self.query_one(SortableDataTable).border_title = str(self.path)
        await self.table.update(self.df)
        await self.table.add_filter(PandasInputFilter(placeholder="Filter"))
        await self.table.add_filter(PandasInputFilter(placeholder="Another filter"))
        await self._add_column_filter(*self.df.columns)

    async def _add_column_filter(self, *columns: str):
        for column in columns:
            values = self.df[column].unique().astype(str)
            cf = PandasSelectFilter(*((c, c, True) for c in values), columns=[column])
            cf.border_title = column
            await self.table.add_filter(cf)

    @on(SelectionList.SelectedChanged)
    async def _update_columns(self, event: SelectionList.SelectedChanged):
        selected = event.selection_list.selected.copy()
        spawn = selected.copy()
        for fb in self.query(PandasSelectFilter):
            if (t := fb.border_title) not in selected:
                await fb.remove()
            else:
                spawn.remove(t)

        await self._add_column_filter(*spawn)
        await self.table.update(self.df[selected] if selected else self.df)


if __name__ == "__main__":
    from argparse import ArgumentParser

    widgets = {
        "basic": ExampleBasic,
        "sort": ExampleSortable,
        "filter": ExampleFilter,  # TODO: Will not work properly with custom data, as selection is hardcoded
        "column": ExampleColumnSelect,
    }
    parser = ArgumentParser()
    parser.add_argument("widget", choices=widgets.keys())
    parser.add_argument("-p", "--path", default=Path(__file__).with_name("data.csv"), type=Path)
    args = parser.parse_args()
    app = widgets[args.widget](args.path).run()
