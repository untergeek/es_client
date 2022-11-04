"""CLI Wrapper used by cli.py"""
import click
from es_client.cli_example import run

if __name__ == '__main__':
    try:
        # This is because click uses decorators, and pylint doesn't catch that
        # pylint: disable=no-value-for-parameter
        run()
    except RuntimeError as e:
        import sys
        print('{0}'.format(e))
        sys.exit(1)