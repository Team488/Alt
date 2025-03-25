import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Alt'
copyright = '2025, Team 488'
author = 'Team 488'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Sphinx extensions
extensions = [
    # Core documentation extensions
    'sphinx.ext.autodoc',      # Auto-generate documentation from docstrings
    'sphinx.ext.napoleon',     # Support for Google and NumPy docstring styles
    'sphinx.ext.viewcode',     # Add source code links in documentation
    'sphinx.ext.todo',         # Support for TODO notes
    'sphinx.ext.inheritance_diagram',  # Generate inheritance diagrams
    
    # Additional useful extensions
    'sphinx.ext.autosummary',  # Create summary tables for modules
    'sphinx.ext.intersphinx',  # Link to other projects' documentation
    'sphinx_copybutton',       # Add copy button to code blocks
    'myst_parser',             # Markdown support
]

# Source file parsing
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Configuration for extensions
autosummary_generate = True
todo_include_todos = True

# Mock imports for external dependencies that might not be available during build
autodoc_mock_imports = [
    'tensorflow', 'ultralytics', 'depthai', 'deep_sort', 'cv2', 'numpy', 'pandas',
    'matplotlib', 'numba', 'robotpy_apriltag', 'robotpy_wpimath', 'pycapnp',
    'pytesseract', 'XTablesClient', 'pynetworktables', 'protobuf', 'scikit_fmm',
    'pyzmq', 'scipy', 'PIL', 'screeninfo', 'ClientStatistics_pb2', 'kivy',
    'tensorrt', 'rknnlite'
]

# Intersphinx configuration (link to other projects' docs)
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
}

# HTML output configuration
html_theme = 'sphinx_rtd_theme'  # Read the Docs theme
html_static_path = ['_static']

# Inheritance diagram configuration
inheritance_graph_attrs = {
    'rankdir': 'TB',  # Top to Bottom layout
}

# Napoleon configuration for docstring parsing
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# Additional configuration
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Diagram generation (requires Graphviz)
graphviz_output_format = 'svg'