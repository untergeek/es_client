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
    8.18.1
"""

from .builder import Builder
from .debug import debug

__all__ = ["Builder", "debug"]
__version__ = "8.18.1"
