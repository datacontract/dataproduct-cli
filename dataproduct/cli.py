import logging
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable, Optional

import typer
from click import Context
from dotenv import find_dotenv, load_dotenv
from rich.console import Console
from typer.core import TyperGroup
from typing_extensions import Annotated

from dataproduct.output.output_format import OutputFormat

console = Console()

debug_option = Annotated[bool, typer.Option(help="Enable debug logging")]

# Order in which top-level commands appear in `dataproduct --help`.
COMMAND_ORDER = ["init", "lint", "publish"]


class OrderedCommands(TyperGroup):
    def list_commands(self, ctx: Context) -> Iterable[str]:
        known = set(COMMAND_ORDER)
        return [c for c in COMMAND_ORDER if c in self.commands] + [c for c in self.commands if c not in known]


app = typer.Typer(
    cls=OrderedCommands,
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
    help="CLI for data products following the Open Data Product Standard (ODPS).",
)


def version_callback(value: bool) -> None:
    if value:
        try:
            version = metadata.version("dataproduct-cli")
        except metadata.PackageNotFoundError:
            version = "0.0.0"
        console.print(version)
        raise typer.Exit()


@app.callback()
def common(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True, help="Print the version and exit."),
    ] = None,
) -> None:
    """dataproduct CLI."""
    load_dotenv(find_dotenv(usecwd=True))


def enable_debug_logging(debug: bool, otherwise_disable_stderr: bool = False) -> None:
    if debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format="%(asctime)s %(levelname)s %(message)s")
    elif otherwise_disable_stderr:
        logging.disable(logging.CRITICAL)


def resolve_output_format(output_format: Optional[OutputFormat], output: Optional[Path]) -> Optional[OutputFormat]:
    if output_format is not None:
        return output_format
    if output is not None:
        return OutputFormat.junit if str(output).endswith(".xml") else OutputFormat.json
    return None


# Register the commands (each module attaches itself to `app`).
from dataproduct import command_init, command_lint, command_publish  # noqa: E402, F401


def main() -> None:
    app()
