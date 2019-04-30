#=========================================================================
# utility.py
#=========================================================================
# This file includes the helper functions that might be useful for
# RTLIR-related passes.
# 
# Author : Peitian Pan
# Date   : Feb 13, 2019

import inspect, copy

#-------------------------------------------------------------------------
# is_of_type
#-------------------------------------------------------------------------

def is_of_type( obj, Type ):
  """
      `obj` is of `Type` iff `obj` has `Type` or is an array of objects
      which are all of `Type`.
  """

  if isinstance( obj, Type ):

    return True

  if isinstance( obj, list ):

    return reduce( lambda x, y: x and is_of_type( y, Type ), obj, True )

  return False

#-------------------------------------------------------------------------
# collect_objs
#-------------------------------------------------------------------------
# Return a list of members of `m` that are or include `Type` objs.

def collect_objs( m, Type, grouped=False ):

  def ungroup_list( obj ):

    assert isinstance( obj, list )

    ret = []

    for _obj in obj:

      if isinstance( _obj, list ):
        ret += ungroup_list( _obj )

      else:
        ret.append( ( _obj._dsl.my_name, _obj ) )

    return ret

  ret = []

  for name, obj in m.__dict__.iteritems():

    if isinstance( name, basestring ) and not name.startswith( '_' ):

      if is_of_type( obj, Type ):

        if isinstance( obj, list ):
          if not grouped:
            ret.extend( ungroup_list( obj ) )
          else:
            ret.append( ( name, obj ) )

        else:
          ret.append( ( name, obj ) )

  return ret

#-------------------------------------------------------------------------
# freeze
#-------------------------------------------------------------------------

def freeze( obj ):
  """Convert potentially mutable objects into immutable objects."""
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj

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
