import click

from src.analyse import ParseTranslationData

# SPECs are downloaded from https://src.fedoraproject.org/lookaside/
# https://src.fedoraproject.org/lookaside/rpm-specs-latest.tar.xz


@click.command()
@click.argument('keyword')
@click.option(
    '--type', help="Parse format, example, SPEC"
)
@click.option(
    '--path', help="Directory path",
    default='/home/suanand/Downloads/rpm-specs-latest/rpm-specs'
)
@click.pass_obj
def find(app_context, keyword, type, path):
    """Find in SPEC file."""
    parse_dict = {"parse": "SPEC"}

    type = 'SPEC' if not type else type.upper()

    # Call find_in api from src module
    some_obj = ParseTranslationData(type, path)
    some_obj.find_in_spec_file(keyword)

    # app_context.print_r(parse_dict)
