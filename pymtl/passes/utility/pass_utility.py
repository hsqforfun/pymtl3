#=========================================================================
# pass_utility.py
#=========================================================================
# This file includes the helper functions that are common to more than
# one passes.
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

#-------------------------------------------------------------------------
# is_obj_eq
#-------------------------------------------------------------------------

def is_obj_eq( obj, other ):
  """Check equity by value instead of ID"""

  def is_in_list( obj, lst ):
    for idx, item in enumerate(lst):
      if is_obj_eq( obj, item ):
        del lst[idx]
        return True
    return False

  if type( obj ) != type( other ): return False

  if isinstance( obj, dict ):
    _other_keys, _other_vals = other.keys(), other.values()
    for key, value in obj.iteritems():
      if not is_in_list( key, _other_keys ):
        return False
      if not is_in_list( value, _other_vals ):
        return False
    return (len(_other_keys) == 0) and (len(_other_vals) == 0)

  if isinstance( obj, set ):
    _other = list( other )
    for _obj in obj:
      if not is_in_list( _obj, _other ):
        return False
    return len( _other ) == 0

  if isinstance( obj, ( list, tuple ) ):
    if len( obj ) != len( other ):
      return False
    for _obj0, _obj1 in zip( obj, other ):
      if not is_obj_eq( _obj0, _obj1 ): return False
    return True

  if not hasattr( obj, '__dict__' ):
    return obj == other

  if len(obj.__dict__.keys()) != len(other.__dict__.keys()):
    return False
  for name, _obj in obj.__dict__.iteritems():
    if not isinstance( name, basestring ) or name.startswith( '_' ):
      continue
    if not name in other.__dict__:                  return False
    if not is_obj_eq( _obj, other.__dict__[name] ): return False
  return True

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
