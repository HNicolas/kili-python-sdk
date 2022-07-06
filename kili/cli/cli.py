"""Kili CLI"""
import click

from kili import __version__
from kili.cli.common_args import CONTEXT_SETTINGS
from kili.cli.project import project_group


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
def cli():
    """Kili Command line Interface

       To get all the available commands, please type: `kili project --help`.
    """


cli.add_command(project_group, name="project")


def main() -> None:
    """Execute the main function of the command line."""
    cli()


if __name__ == "__main__":
    main()
