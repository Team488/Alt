# Alt Documentation

This directory contains the Sphinx documentation for the Alt codebase.

## Building the Documentation

To build the documentation, follow these steps:

1. Install Sphinx and required extensions:
   ```bash
   pip install -r docs/requirements.txt
   ```

2. From the docs directory, run:
   ```bash
   make html
   ```

3. The built documentation can be found in the `_build/html` directory.

## Documentation Structure

- `conf.py`: Sphinx configuration file
- `index.rst`: Main documentation entry point
- `modules/`: Contains RST files for documenting different modules
- `_build/`: Contains the built documentation (after running `make html`)
- `_static/`: Static files (CSS, images, etc.)
- `_templates/`: Custom Sphinx templates

## Adding Documentation

The documentation is generated from docstrings in the code. We follow Google-style 
docstrings, which are processed by the `sphinx.ext.napoleon` extension. See examples
in the codebase for the correct format.

A helper script `add_sphinx_docstrings.py` is available to identify files that need
documentation.

## Conventions

- Module docstrings at the top of each file
- Class docstrings with Attributes sections
- Method docstrings with Args, Returns, Raises sections
- Enum docstrings with descriptions of each value