"""Sphinx configuration for es_client documentation.

Configures Sphinx to generate documentation for the es_client package,
using autodoc, Napoleon, doctest, viewcode, and intersphinx extensions.
Imports metadata (__version__, __author__, __copyright__) from
es_client, leveraging module installation for ReadTheDocs. Sets up
GitHub integration for "Edit Source" links and supports Python 3.8-3.13.

Attributes:
    project: Project name ("es_client"). (str)
    author: Author name from es_client.__author__. (str)
    version: Major.minor version (e.g., "1.3"). (str)
    release: Full version (e.g., "1.3.0"). (str)
    html_theme: Theme for HTML output, defaults to "furo". (str)

Examples:
    >>> project
    'es_client'
    >>> author
    'Aaron Mildenstein'
    >>> version
    '1.3'
    >>> 'autodoc' in [ext.split('.')[-1] for ext in extensions]
    True
"""

# pylint: disable=C0103,E0401,W0622

# -- Imports and setup -----------------------------------------------------

from es_client import __author__, __copyright__, __version__

# -- Project information -----------------------------------------------------

project = "es_client"
github_user = "untergeek"
github_repo = "es_client"
github_branch = "master"
author = __author__
copyright = __copyright__
release = __version__
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build"]
source_suffix = ".rst"
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"

# Add "Edit Source" links into the template
html_context = {
    "display_github": True,
    "github_user": f"{github_user}",
    "github_repo": f"{github_repo}",
    "github_version": f"{github_branch}",
    "conf_py_path": "/docs/",  # Path in the checkout to the docs root
}

# -- Autodoc configuration ---------------------------------------------------

autoclass_content = "both"
autodoc_class_signature = "separated"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- Intersphinx configuration -----------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.13", None),
    "elasticsearch9": ("https://elasticsearch-py.readthedocs.io/en/v9.1.1", None),
    "elastic-transport": (
        "https://elastic-transport-python.readthedocs.io/en/stable",
        None,
    ),
    "voluptuous": ("http://alecthomas.github.io/voluptuous/docs/_build/html", None),
    "click": ("https://click.palletsprojects.com/en/stable", None),
}
