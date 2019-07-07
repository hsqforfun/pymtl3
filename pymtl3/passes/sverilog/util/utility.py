#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to sverilog passes."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir.util.utility import get_component_full_name


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_component_unique_name( c_rtype ):

  full_name = get_component_full_name( c_rtype )

  if len(full_name) < 64:
    return full_name

  comp_name = c_rtype.get_name()
  param_name = str(abs(hash(full_name[len(comp_name):])))
  return comp_name + "__" + param_name
