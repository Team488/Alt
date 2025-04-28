# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Alt'
copyright = '2025, The Matrix 488'
author = 'The Matrix 488'
release = '2025'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',        # for Google docstrings
    'sphinx_autodoc_typehints',    # for cleaner type hints
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


# Make sure Python finds your modules:
import os
import sys
sys.path.insert(0, os.path.abspath('../../Alt-Core/src'))
sys.path.insert(0, os.path.abspath('../../Alt-Cameras/src'))
