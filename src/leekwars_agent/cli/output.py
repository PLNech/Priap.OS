"""Output formatting utilities for CLI."""

import json
import click
from rich.console import Console
from rich.table import Table

console = Console()


def output_json(data: dict | list) -> None:
    """Output data as JSON."""
    click.echo(json.dumps(data, indent=2, default=str))


def output_table(title: str, columns: list[str], rows: list[list]) -> None:
    """Output data as a rich table."""
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)


def output_kv(data: dict, title: str | None = None) -> None:
    """Output key-value pairs."""
    if title:
        console.print(f"[bold]{title}[/bold]")
    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")


def success(msg: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {msg}")


def error(msg: str) -> None:
    """Print error message."""
    console.print(f"[red]✗[/red] {msg}")


def warning(msg: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]![/yellow] {msg}")
