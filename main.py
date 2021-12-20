#!/usr/bin/env python3

from library import *

import logging
import click
import os


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.argument('dest', nargs=1, type=click.Path(exists=True))
def do_rename_dedup(files, dest):
    logging.info("=== Start ===")
    rename_files(files, dest)
    dedup_dir(dest)
    logging.info("===  End  ===")


if __name__ == '__main__':
    logging.basicConfig(
        filename=os.path.join(os.getenv('DATADIR'), 'mr_log.log'),
        format='%(asctime)s; %(name)s; %(levelname)s; %(message)s',
        level=logging.INFO
    )
    do_rename_dedup()
