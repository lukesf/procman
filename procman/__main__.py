import sys
import click
from .sheriff.gui import main as sheriff_gui_main
from .sheriff.cli import cli as sheriff_cli
from .deputy.deputy import main as deputy_main


@click.group()
def cli():
    """Process Manager - A distributed process management system"""
    pass


@cli.group()
def sheriff():
    """Sheriff process manager commands"""
    pass


@sheriff.command(name="gui")
def sheriff_gui():
    """Start the Sheriff GUI"""
    sheriff_gui_main()


# Add the CLI commands from sheriff.cli
sheriff.add_command(sheriff_cli, name="cli")


@cli.command(name="deputy")
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
def deputy_cmd(host: str, port: int):
    """Start the Deputy process manager"""
    deputy_main(host=host, port=port)


def main():
    """Main entry point for the application."""
    cli()


if __name__ == "__main__":
    main() 