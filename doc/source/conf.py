# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../pysui"))
import pysui


project = "pysui"
copyright = "2022, Frank V. Castellucci"
author = "Frank V. Castellucci"
version = pysui.version.__version__
release = version
# release = pysui.version.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "temp"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "display_version": True,
    "sticky_navigation": False,
    "navigation_depth": 5,
    # "includehidden": False,
    # "titles_only": False,
}

# html_static_path = ["_static"]
html_static_path = []
