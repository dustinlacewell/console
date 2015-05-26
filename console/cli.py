from os import environ as env

from attrdict import AttrDict

import click

from console.app import app
from console.ui.layout import RootFrame


@click.command()
@click.option('--host',
              envvar='DOCKER_HOST',
              default='unix://var/run/docker.sock')
@click.option('--freq', default=.25)
@click.option('--debug', default=False)
@click.pass_context
def main(ctx, *args, **kwargs):
    app.init(AttrDict(kwargs), RootFrame)
    app.run()
