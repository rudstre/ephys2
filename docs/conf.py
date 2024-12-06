# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
from datetime import date
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'ephys2'
copyright = f'2021-{date.today().year}, Harvard University'
author = 'Harvard University'

# The full version, including alpha/beta/rc tags
version = '1.0.0'
release = '1.0.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
	'myst_parser',
	'sphinx.ext.autodoc',
  'sphinx.ext.mathjax',
	'sphinx_gallery.gen_gallery',
	'sphinx.ext.autosectionlabel',
	'sphinx_design',
]

# Sphinx-gallery outputs
sphinx_gallery_conf = {
	'examples_dirs': [
		'examples',   # path to your example scripts
		'stages',
	],
	'gallery_dirs': [
		'built_examples',  # path to where to save gallery generated output
		'built_stages',
	],
	'download_all_examples': False,
	'image_scrapers': ('matplotlib',),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = ['.rst', '.md']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'
# highlight_language = 'python3'

# The master toctree document.
master_doc = 'index'

# See warnings about bad links
nitpicky = True
nitpick_ignore = [('', "Pygments lexer name 'ipython' is not known")]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = True

html_css_files = [
	'css/nodownload.css',
]