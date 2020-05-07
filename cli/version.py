import click


@click.command()
@click.pass_obj
def version(app_context):
    """Display the current version."""
    version_dict = {"cli": "version %s" % app_context.version}
    app_context.print_r(version_dict)
