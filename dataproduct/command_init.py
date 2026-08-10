import os

import typer
from typing_extensions import Annotated

from dataproduct.cli import app, console, debug_option, enable_debug_logging
from dataproduct.init.init_template import get_init_template


@app.command(
    name="init",
    epilog="Example: dataproduct init dataproduct.odps.yaml",
)
def init(
    location: Annotated[
        str, typer.Argument(help="The location of the data product file to create.")
    ] = "dataproduct.odps.yaml",
    template: Annotated[str, typer.Option(help="URL or path of a template or data product")] = None,
    overwrite: Annotated[bool, typer.Option(help="Replace the existing data product file")] = False,
    debug: debug_option = None,
):
    """
    Create a new data product file.
    """
    enable_debug_logging(debug)

    if not overwrite and os.path.exists(location):
        console.print("File already exists, use --overwrite to overwrite")
        raise typer.Exit(code=1)
    template_str = get_init_template(template)
    with open(location, "w") as f:
        f.write(template_str)
    console.print("📄 data product written to " + location)
