# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PolyPlug'
copyright = '2023, Anaconda Inc.'
author = 'Anaconda Inc.'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc", "sphinx.ext.viewcode", "myst_parser",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

source_suffix = [".rst", ".md",]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    "description": "Browser interaction for WASM based scripting languages.",
    "logo_name": True,
    "logo_text_align": "center",
    "github_user": "pyscript",
    "github_repo": "polyplug",
}
html_sidebars = {"*": ["about.html", "navigation.html", "searchbox.html"]}
html_static_path = ['_static']
html_logo = "icon.png"
