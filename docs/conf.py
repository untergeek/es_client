"""Sphinx Documentation Configuration"""

# pylint: disable=C0103,C0114,E0401,W0611,W0622

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os
from datetime import datetime

COPYRIGHT_YEARS = f"2022-{datetime.now().year}"

# Extract the version from the __init__.py file

path = "../src/es_client/__init__.py"
myinit = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)

ver = ""
with open(myinit, "r", encoding="utf-8") as file:
    lines = file.readlines()

for line in lines:
    if line.startswith("__version__"):
        ver = line.split('"')[1]


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "es_client"
author = "Aaron Mildenstein"
copyright = f"{COPYRIGHT_YEARS}, {author}"
release = ver
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
]
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]
source_suffix = ".rst"
master_doc = "index"

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
]
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]
source_suffix = ".rst"
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

pygments_style = "sphinx"

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only import and set the theme if we're building docs locally
    html_theme = "sphinx_rtd_theme"

# -- Autodoc configuration ---------------------------------------------------


autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.12", None),
    "elasticsearch8": ("https://elasticsearch-py.readthedocs.io/en/v8.18.0", None),
    "elastic-transport": (
        "https://elastic-transport-python.readthedocs.io/en/stable",
        None,
    ),
    "voluptuous": ("http://alecthomas.github.io/voluptuous/docs/_build/html", None),
    "click": ("https://click.palletsprojects.com/en/8.1.x", None),
}
