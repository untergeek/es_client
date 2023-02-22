"""Sphinx Documentation Configuration"""
# -*- coding: utf-8 -*-
#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.

# pylint: disable=redefined-builtin, invalid-name
import sys
import os
from datetime import datetime
from es_client import __version__ as ver

COPYRIGHT_YEARS = f'2022-{datetime.now().year}'

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.intersphinx']

autoclass_content = "both"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'es_client'
author = 'Aaron Mildenstein'
copyright = f'{COPYRIGHT_YEARS}, Aaron Mildenstein'

release = ver
version = '.'.join(release.split('.')[:2])

exclude_patterns = ['_build']

pygments_style = "sphinx"

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

intersphinx_mapping = {
	'python': ('https://docs.python.org/3.11', None),
	'elasticsearch8': ('https://elasticsearch-py.readthedocs.io/en/v8.6.1', None),
    'elastic-transport': ('https://elastic-transport-python.readthedocs.io/en/stable', None),
    'voluptuous': ('http://alecthomas.github.io/voluptuous/docs/_build/html', None),
    'click': ('https://click.palletsprojects.com/en/8.1.x', None),
}
