"""
es_client Module Initialization

This module initializes the es_client package, providing utilities for building
Elasticsearch client connections and debugging tools.

Exported Objects:
    - Builder: A class to construct Elasticsearch client connections.
    - debug: A debugging utility for logging at various verbosity levels.

Example Usage:
    >>> from es_client import Builder
    >>> config = {'elasticsearch': {'client': {'hosts': ['http://localhost:9200']}}}
    >>> builder = Builder(configdict=config)
    >>> builder.client_args.hosts
    ['http://localhost:9200']
    >>> from es_client import debug
    >>> debug.lv1("Debug message")
    # Outputs debug message at level 1, if logging is configured appropriately.

Version:
    8.19.4
"""

from datetime import datetime
from .builder import Builder
from .debug import debug

FIRST_YEAR = 2022
now = datetime.now()
if now.year == FIRST_YEAR:
    COPYRIGHT_YEARS = "2025"
else:
    COPYRIGHT_YEARS = f"2025-{now.year}"

__version__ = "8.19.4"
__author__ = "Aaron Mildenstein"
__copyright__ = f"{COPYRIGHT_YEARS}, {__author__}"
__license__ = "Apache 2.0"
__status__ = "Development"
__description__ = "Elasticsearch Client builder, complete with schema validation"
__url__ = "https://github.com/untergeek/es_client"
__email__ = "aaron@mildensteins.com"
__maintainer__ = "Aaron Mildenstein"
__maintainer_email__ = f"{__email__}"
__keywords__ = ["elasticsearch", "client", "connect", "command-line"]
__classifiers__ = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

__all__ = ["Builder", "debug", "__author__", "__copyright__", "__version__"]
