from pathlib import Path

import typer
from typing_extensions import Annotated

from dataproduct.cli import app, console, debug_option, enable_debug_logging, resolve_output_format
from dataproduct.config import cli_config
from dataproduct.data_product import DataProduct
from dataproduct.output.output_format import OutputFormat
from dataproduct.output.result_writer import write_result


@app.command(
    name="lint",
    epilog="Example: dataproduct lint dataproduct.odps.yaml",
)
def lint(
    location: Annotated[
        str,
        typer.Argument(help="The location (url or local path) of the data product yaml."),
    ] = "dataproduct.odps.yaml",
    schema: Annotated[
        str,
        typer.Option("--json-schema", help="The location (url or path) of the ODPS JSON Schema"),
    ] = None,
    output: Annotated[
        Path,
        typer.Option(
            help="File path to write the results to (e.g. './TEST-dataproduct.xml'). "
            "If omitted, results are printed to stdout."
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option(help="The result format. Accepted values: json, junit."),
    ] = None,
    all_errors: Annotated[
        bool,
        typer.Option(
            "--all-errors",
            help="Report all JSON Schema validation errors instead of stopping after the first one.",
        ),
    ] = False,
    debug: debug_option = None,
):
    """
    Validate that the data product is correctly formatted (against the ODPS JSON Schema).
    """
    enable_debug_logging(debug, otherwise_disable_stderr=True)

    output_format = resolve_output_format(output_format, output)
    run = DataProduct(
        config=cli_config(),
        data_product_file=location,
        schema_location=schema,
        all_errors=all_errors,
    ).lint()
    write_result(run, console, output_format, output)
