#!/usr/bin/env python3

from library import *

import logging
import click
import os
import datetime


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument('input_dir', nargs=1, type=click.Path(exists=True))
@click.argument('output_dir', nargs=1, type=click.Path(exists=True))
def do_rename_dedup(input_dir, output_dir):
    logging.info("=== Start ===")
    convert_heic_dir(input_dir)
    rename_files(input_dir, output_dir)
    dedup_dir(output_dir)
    logging.info("===  End  ===")


if __name__ == '__main__':
    logging.basicConfig(
        filename='{}/mrn_{}.log'.format(os.getenv('DATA_DIR', '.'), datetime.datetime.today().strftime('%Y%m%d')),
        format='%(asctime)s; %(name)s; %(levelname)s; %(message)s',
        level=logging.INFO
    )
    do_rename_dedup()
