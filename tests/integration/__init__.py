"""Integration setup"""

from os import environ
from es_client.debug import debug

HOST = environ.get("TEST_ES_SERVER", "https://127.0.0.1:9200")
USER = environ.get("TEST_USER", "elastic")
PASS = environ.get("TEST_PASS")
CACRT = environ.get("CA_CRT")

debug.level = 5
