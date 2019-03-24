#=========================================================================
# utility.py
#=========================================================================
# This file includes utility functions that might be helpful to the
# translation framework.
#
# Author : Peitian Pan
# Date   : March 12, 2019

from collections import defaultdict, deque

from pymtl       import *
from pymtl.passes.utility import freeze

#-------------------------------------------------------------------------
# gen_connections
#-------------------------------------------------------------------------

def gen_connections( top ):
  """Get all modules in the component hierarchy and analyze all
  reader-writer relations. These are needed to gen the
  continuous assignment statements."""

  nets = top.get_all_nets()
  adjs = top.get_signal_adjacency_dict()

  connections = {}

  connections['self_child']  = defaultdict(set)
  connections['self_self']   = defaultdict(set)
  connections['child_child'] = defaultdict(set)

  for writer, net in nets:
    S = deque( [ writer ] )
    visited = set( [ writer ] )
    while S:
      u = S.pop()
      writer_host        = u.get_host_component()
      writer_host_parent = writer_host.get_parent_object() 

      for v in adjs[u]:
        if v not in visited:
          visited.add( v )
          S.append( v )
          reader_host        = v.get_host_component()
          reader_host_parent = reader_host.get_parent_object()

          # Four possible cases for the reader and writer signals:
          # 1.   They have the same host component. Both need 
          #       to be added to the host component.
          # 2/3. One's host component is the parent of the other.
          #       Both need to be added to the parent component.
          # 4.   They have the same parent component.
          #       Both need to be added to the parent component.

          if writer_host is reader_host:
            connections['self_self'][ writer_host ].add( ( u, v ) )

          elif writer_host_parent is reader_host:
            connections['self_child'][ reader_host ].add( ( u, v ) )

          elif writer_host is reader_host_parent:
            connections['self_child'][ writer_host ].add( ( u, v ) )

          elif writer_host_parent == reader_host_parent:
            connections['child_child'][ writer_host_parent ].add( ( u, v ) )

          else: assert False

  return connections

#-------------------------------------------------------------------------
# get_topmost_member
#-------------------------------------------------------------------------

def get_topmost_member( model, signal ):

  sig = signal

  while not isinstance(sig._dsl.parent_obj, RTLComponent):
    sig = sig._dsl.parent_obj

  return sig

#-------------------------------------------------------------------------
# is_BitsX
#-------------------------------------------------------------------------

def is_BitsX( obj ):
  """Is obj a BitsX class?"""

  try:
    if obj.__name__.startswith( 'Bits' ):
      try:
        n = int( obj.__name__[4:] )
        return True
      except:
        return False
  except:
    return False

  return False

#-------------------------------------------------------------------------
# freeze
#-------------------------------------------------------------------------

def freeze( obj ):

  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj
