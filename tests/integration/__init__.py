"""Integration setup"""

from os import environ

HOST = environ.get("TEST_ES_SERVER", "https://127.0.0.1:9200")
USER = environ.get("TEST_USER", "elastic")
PASS = environ.get("TEST_PASS")
CACRT = environ.get("CA_CRT")
