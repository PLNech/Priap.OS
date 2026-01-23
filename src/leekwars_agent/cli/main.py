"""LeekWars CLI - main entry point."""

import click
from .commands import info, craft, fight, market


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON (for automation)")
@click.version_option(version="0.1.0", prog_name="leek")
@click.pass_context
def cli(ctx: click.Context, json_output: bool) -> None:
    """LeekWars CLI - fight, craft, and manage your leek.

    Use --json flag with any command for machine-readable output.

    Examples:

        leek info leek                    # Show your leek's stats

        leek craft inventory --json       # List components (JSON)

        leek fight status                 # Show fights remaining
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output


# Register command groups
cli.add_command(info.info)
cli.add_command(craft.craft)
cli.add_command(fight.fight)
cli.add_command(market.market)


def main() -> None:
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
