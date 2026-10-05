"""Render a :class:`Run` to the console or a machine-readable file.

Console output uses ``rich``; ``--output-format json|junit`` writes a file (or
stdout). A failed run exits with code 1.
"""

from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import Element, SubElement, tostring

import typer
from rich.markup import escape

from dataproduct.model.run import ResultEnum, Run
from dataproduct.output.output_format import OutputFormat

_ICON = {
    ResultEnum.passed: "✅",
    ResultEnum.warning: "⚠️ ",
    ResultEnum.error: "❌",
    ResultEnum.failed: "❌",
}


def write_result(run: Run, console, output_format: Optional[OutputFormat], output: Optional[Path]) -> None:
    if output_format == OutputFormat.json:
        _write_or_print(run.model_dump_json(indent=2), output, console)
    elif output_format == OutputFormat.junit:
        _write_or_print(_to_junit(run), output, console)
    else:
        _print_console(run, console)

    if not run.has_passed():
        raise typer.Exit(code=1)


def _print_console(run: Run, console) -> None:
    for check in run.checks:
        icon = _ICON.get(check.result, "•")
        line = f"{icon} {escape(check.name)}"
        if check.reason:
            line += f": {escape(check.reason)}"
        console.print(line)
    if run.has_passed():
        console.print("[green]🟢 Data product is valid.[/green]")
    else:
        console.print("[red]🔴 Data product is invalid.[/red]")


def _write_or_print(content: str, output: Optional[Path], console) -> None:
    if output is not None:
        Path(output).write_text(content)
        console.print(f"📝 results written to {output}")
    else:
        print(content)


def _to_junit(run: Run) -> str:
    failures = sum(1 for c in run.checks if c.result in (ResultEnum.error, ResultEnum.failed))
    testsuite = Element(
        "testsuite",
        {
            "name": "dataproduct-lint",
            "tests": str(len(run.checks)),
            "failures": str(failures),
            "errors": "0",
        },
    )
    for check in run.checks:
        testcase = SubElement(
            testsuite,
            "testcase",
            {"classname": check.type, "name": check.name},
        )
        if check.result in (ResultEnum.error, ResultEnum.failed):
            failure = SubElement(testcase, "failure", {"message": check.reason or check.name})
            failure.text = check.reason or check.name
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(testsuite, encoding="unicode")
