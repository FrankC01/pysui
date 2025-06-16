# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import unittest.mock as mock

MOCK_MODULES = ["pysui_fastcrypto", "pysui_fastcrypto"]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = mock.Mock()

autodoc_mock_imports = ["pysui-fastcrypto"]


sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("../../pysui"))
import pysui


project = "pysui"
copyright = "Frank V. Castellucci"
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
    "navigation_depth": 9,
    # "includehidden": False,
    # "titles_only": False,
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# html_static_path = ["_static"]
html_static_path = []
