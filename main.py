#!/usr/bin/env python

from library import *
import logging
from datetime import datetime


if __name__ == '__main__':
    logging.basicConfig(
        filename='log/renamer_{}.log'.format(datetime.today().strftime('%Y%m%d')),
        format='%(asctime)s; %(name)s; %(levelname)s; %(message)s',
        level=logging.INFO
    )

    logging.info("=== Start ===")
    logging.info(datetime.now())
    rename_files()
    logging.info("=== End ===")
