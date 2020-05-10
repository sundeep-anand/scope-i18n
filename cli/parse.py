import click

from src.TranslationData import ParseTranslationData

@click.command()
@click.option(
    '--type', help="Parse format, example, SPEC"
)
@click.option(
    '--path', help="Directory path", 
    default='/home/suanand/Downloads/rpm-specs-latest/rpm-specs'
)
@click.pass_obj
def parse(app_context, type, path):
    """Parse SPEC file."""
    parse_dict = {"parse": "SPEC"}

    type = 'SPEC' if not type else type.upper()

    # Call parse api from src module
    some_obj = ParseTranslationData(type, path)
    some_obj.parse_spec_file()

    # app_context.print_r(parse_dict)
