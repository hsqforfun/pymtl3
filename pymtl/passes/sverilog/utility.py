#=========================================================================
# utility.py
#=========================================================================
# This file includes the helper functions that might be useful for
# SystemVerilog backend passes.
# 
# Author : Peitian Pan
# Date   : Feb 13, 2019

import inspect, copy

#-------------------------------------------------------------------------
# make_indent
#-------------------------------------------------------------------------

def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '

  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

#-------------------------------------------------------------------------
# get_string
#-------------------------------------------------------------------------

def get_string( obj ):
  """Return the string that identifies `obj`"""
  if inspect.isclass( obj ): return obj.__name__
  return str( obj )
