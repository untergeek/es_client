#!/usr/bin/env python
"""Script to run locally"""

from click import echo
from es_client.cli_example import run

if __name__ == '__main__':
    try:
        # This is because click uses decorators, and pylint doesn't catch that
        # pylint: disable=no-value-for-parameter
        run()
    except RuntimeError as err:
        import sys

        echo(f'{err}')
        sys.exit(1)
