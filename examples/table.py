from textual.app import App
from textual_pandas.widgets import DataTable, SortableDataTable, TextFilterDataTable


def example_factory(widget, df):
    class Example(App):
        def compose(self):
            yield widget()

        async def on_mount(self):
            frame = self.query_one(widget)
            await frame.update(df)  # type: ignore

    return Example()


if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path

    from pandas import read_csv

    widgets = {
        "mini": DataTable,
        "sortable": SortableDataTable,
        "filter": TextFilterDataTable,
    }
    parser = ArgumentParser()
    parser.add_argument("widget", choices=widgets.keys())
    parser.add_argument("-p", "--path", default=Path(__file__).with_name("data.csv"), type=Path)
    args = parser.parse_args()

    example_factory(widgets[args.widget], read_csv(args.path)).run()
