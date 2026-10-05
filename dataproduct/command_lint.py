from pathlib import Path

import typer
from typing_extensions import Annotated

from dataproduct.cli import app, console, debug_option, enable_debug_logging, resolve_output_format
from dataproduct.config import cli_config
from dataproduct.data_product import DataProduct
from dataproduct.lint.contract_lint import datacontract_cli_path
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
    resolve_references: Annotated[
        bool,
        typer.Option(
            help="Resolve the data contracts linked via input/output port contractId (via Entropy Data when an "
            "API key is set, else among *.odcs.yaml files under the current directory) and, if datacontract-cli "
            "is on the PATH, lint them with it."
        ),
    ] = True,
    local_references: Annotated[
        bool,
        typer.Option(
            "--local-references",
            help="Resolve the linked data contracts among *.odcs.yaml files under the current directory, even when "
            "an Entropy Data API key is set.",
        ),
    ] = False,
    debug: debug_option = None,
):
    """
    Validate that the data product is correctly formatted (against the ODPS JSON Schema) and that its linked
    data contracts resolve.
    """
    enable_debug_logging(debug, otherwise_disable_stderr=True)

    output_format = resolve_output_format(output_format, output)
    run = DataProduct(
        config=cli_config(),
        data_product_file=location,
        schema_location=schema,
        all_errors=all_errors,
        resolve_references=resolve_references,
        local_references=local_references,
        datacontract_cli=datacontract_cli_path() if resolve_references else None,
    ).lint()
    write_result(run, console, output_format, output)
