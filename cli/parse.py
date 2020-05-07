import click

from src.TranslationData import ParseTranslationData

@click.command()
@click.pass_obj
def parse(app_context):
    """Parse SPEC file."""
    parse_dict = {"parse": "SPEC"}
    
    # Call parse api from src module
    some_obj = ParseTranslationData()
    some_obj.do_something()

    app_context.print_r(parse_dict)
