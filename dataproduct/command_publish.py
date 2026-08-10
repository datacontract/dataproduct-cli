import typer
from typing_extensions import Annotated

from dataproduct.cli import app, console, debug_option, enable_debug_logging
from dataproduct.config import cli_config
from dataproduct.integration.entropy_data import (
    DataProductPublishError,
    publish_data_product_to_entropy_data,
)
from dataproduct.lint.resolve import resolve_data_product_dict
from dataproduct.model.exceptions import DataProductException


@app.command(
    name="publish",
    epilog="Example: dataproduct publish dataproduct.odps.yaml",
)
def publish(
    location: Annotated[
        str,
        typer.Argument(help="The location (url or local path) of the data product yaml."),
    ] = "dataproduct.odps.yaml",
    schema: Annotated[
        str,
        typer.Option("--json-schema", help="The location (url or path) of the ODPS JSON Schema"),
    ] = None,
    ssl_verification: Annotated[
        bool,
        typer.Option(help="SSL verification when publishing the data product."),
    ] = True,
    debug: debug_option = None,
):
    """
    Publish the data product to Entropy Data.
    """
    enable_debug_logging(debug)

    try:
        data_product_dict = resolve_data_product_dict(location, config=cli_config())
        publish_data_product_to_entropy_data(
            data_product_dict=data_product_dict,
            ssl_verification=ssl_verification,
            config=cli_config(),
        )
    except (DataProductPublishError, DataProductException) as e:
        console.print(f"[red]Failed publishing data product. Error: {e}[/red]")
        raise typer.Exit(code=1)
