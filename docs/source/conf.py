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
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",           # For Google/NumPy style docstrings
    "sphinx.ext.viewcode",           # Adds source code links
    "sphinx.ext.autosummary",        # Enables autosummary tables
    "sphinx_autodoc_typehints",      # Type hint support (optional)
    "sphinx_markdown_parser",        # for parsing READMEs
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
autosummary_generate = True          # Auto-generate .rst files for modules

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


# Make sure Python finds your modules:
import os
import sys

BASE = os.path.abspath(os.path.join("..", ".."))
sys.path.insert(0, os.path.join(BASE, "Alt-Core", "src"))
sys.path.insert(0, os.path.join(BASE, "Alt-Cameras", "src"))
sys.path.insert(0, os.path.join(BASE, "Alt-Dashboard", "src"))
sys.path.insert(0, os.path.join(BASE, "Alt-ObjectLocalization", "src"))
sys.path.insert(0, os.path.join(BASE, "Alt-Pathplanning", "src"))


