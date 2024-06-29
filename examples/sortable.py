from pathlib import Path

from pandas import DataFrame, read_csv
from textual.app import App
from textual_pandas.widgets.table import SortableDataTable


class Sortable(App):
    CSS_PATH = "table.tcss"

    def __init__(self, path: Path):
        self.path = path
        self.df: DataFrame = read_csv(path)
        super().__init__()

    def compose(self):
        yield SortableDataTable()

    async def on_mount(self):
        frame = self.query_one(SortableDataTable)
        frame.border_title = str(self.path)
        await frame.update(self.df)  # type: ignore
