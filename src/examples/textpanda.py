import pandas as pd
from textual import on
from textual.widgets import DataTable


class DataFrame(DataTable):
    async def update(self, data: pd.DataFrame, index: str = "Index", height: int | None = 1):
        self.clear(columns=True)
        self.add_columns(index, *data.columns)
        for row in data.itertuples():
            self.add_row(*row, height=height)


class SortableDataFrame(DataFrame):
    def __init__(self, data: pd.DataFrame | None = None, **kwargs):
        super().__init__(**kwargs)
        self.data = data or pd.DataFrame()
        self._sorted: str | None = None

    async def update(self, data: pd.DataFrame, index: str = "Index", height: int | None = 1):
        self.data = data
        await super().update(data, index, height)

    @on(DataTable.HeaderSelected)
    async def _on_header_selected(self, event: DataTable.HeaderSelected):
        name = str(event.label)
        params = {  # NOTE: inplace=True would make sense in some use cases
            "ascending": name != self._sorted,
            "key": lambda x: x.astype(str) if x.dtype == "object" else x,
        }
        if event.column_index:
            self.data = self.data.sort_values(by=name, **params)  # type: ignore
        else:
            self.data = self.data.sort_index(**params)  # type: ignore
        self._sorted = name if name != self._sorted else None
        await self.update(self.data)


if __name__ == "__main__":
    from argparse import ArgumentParser
    from random import choices

    from rich.text import Text
    from textual.app import App
    from textual.widgets import RadioButton, RadioSet

    POP = (Text("Pass", "#00FF00"), Text("Error", "#FFA500"), Text("Fail", "#FF0000"), Text("Skip", "#0000FF"))
    DATA = {k: pd.DataFrame({f"run-{n}": choices(POP, k=10) for n in range(3)}) for k in "abc"}

    class MinimalExample(App):
        def compose(self):
            yield DataFrame()

        async def on_mount(self):
            frame = self.get_child_by_type(DataFrame)
            await frame.update(DATA["a"])

    class SortableExample(App):
        def compose(self):
            yield SortableDataFrame()

        async def on_mount(self):
            frame = self.get_child_by_type(SortableDataFrame)
            await frame.update(DATA["a"])

    class SelectExample(App):
        DEFAULT_CSS = """
            RadioSet {
                height: 5;
            }
            DataTable {
                max-height: 70%;
                min-height: 5;
            }
        """

        def compose(self):
            yield RadioSet(*map(RadioButton, DATA.keys()))
            yield SortableDataFrame()

        @on(RadioSet.Changed)
        async def _on_radio(self, event: RadioSet.Changed):
            frame = self.get_child_by_type(SortableDataFrame)
            await frame.update(DATA[event.pressed.label.__str__()])

    applications = {
        "mini": MinimalExample,
        "sort": SortableExample,
        "select": SelectExample,
    }
    parser = ArgumentParser()
    parser.add_argument("example", choices=applications.keys())
    args = parser.parse_args()
    applications[args.example]().run()
