import json
import click

from cli.version import version
from cli.parse import parse
from cli.find import find

APP_VERSION = "0.1.0"


class AppContext(object):
    """
    CLI Application Context Data
    """
    def __init__(self):
        self.version = APP_VERSION

    @staticmethod
    def print_r(result_dict):
        click.echo(json.dumps(result_dict, indent=4, sort_keys=True))


@click.group()
@click.pass_context
def entry_point(ctx):
    """
    Scope i18n CLI
    """
    ctx.obj = AppContext()


entry_point.add_command(version)
entry_point.add_command(parse)
entry_point.add_command(find)
