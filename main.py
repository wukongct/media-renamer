#!/usr/bin/env python

from library import *

import logging
import click
import os

from datetime import datetime


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.argument('dest', nargs=1, type=click.Path(exists=True))
def do_rename_dedup(files, dest):
    logging.info("=== Start ===")
    rename_files(files, dest)
    dedup_dir(dest)
    logging.info("===  End  ===")


if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    logging.basicConfig(
        filename=os.path.join(home_dir, 'log/renamer_{}.log'.format(datetime.today().strftime('%Y%m%d'))),
        format='%(asctime)s; %(name)s; %(levelname)s; %(message)s',
        level=logging.INFO
    )
    do_rename_dedup()

