#=========================================================================
# BehavioralRTLIRTypeL1.py
#=========================================================================
# This file contains all RTLIR types in its type system.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

import inspect

from pymtl                             import *
from pymtl.passes.utility.pass_utility import freeze, is_obj_eq

from ..utility import is_BitsX

#-------------------------------------------------------------------------
# Base RTLIR Type
#-------------------------------------------------------------------------

class BaseBehavioralRTLIRType( object ):
  def __new__( cls, *args, **kwargs ):
    return super( BaseBehavioralRTLIRType, cls ).__new__( cls )

  def __init__( s ):
    super( BaseBehavioralRTLIRType, s ).__init__()

  #-----------------------------------------------------------------------
  # get_type
  #-----------------------------------------------------------------------

  @staticmethod
  def get_type( obj ):
    """return the RTLIR type of obj"""

    if isinstance( obj, RTLComponent ):

      type_env = {}

      BaseBehavioralRTLIRType.get_type_attributes( obj, type_env )

      return Module( obj, type_env )

    # Signals might be parameterized by different types
    elif isinstance( obj, ( InVPort, OutVPort, Wire ) ):
      
      # BitsX
      if is_BitsX( obj._dsl.Type ):
        nbits = obj._dsl.Type.nbits
        return Signal( nbits, obj.__class__.__name__ )

      assert False, "Unsupported signal type {} at L1".format( obj._dsl.Type )

    # integers have unset bitwidth (0) 
    elif isinstance( obj, int ):
      return Const( True, 0, obj )

    # Bits instances
    elif isinstance( obj, Bits ):
      return Const( True, obj.nbits, obj.value )

    # array type
    elif isinstance( obj, list ):
      assert len( obj ) > 0

      type_env = {}

      type_list = map( lambda x: BaseBehavioralRTLIRType.get_type( x ), obj )

      assert reduce(lambda x, y: x and (y == type_list[0]), type_list, True),\
        'Elements of list ' + str(obj) + ' must have the same RTLIR type!'

      for _obj, _Type in zip( obj, type_list ):
        type_env[ _obj ] = _Type
        try:
          type_env.update( _Type.type_env )
        except:
          pass

      ret = Array( len( obj ), type_list[0] )
      ret.type_env = type_env

      return ret

    elif inspect.isclass( obj ):

      # BitsX
      if is_BitsX( obj ):
        nbits = obj.nbits
        return Signal( nbits )

    assert False, 'unsupported object ' + str(obj) + '!'

  #-----------------------------------------------------------------------
  # get_type_attributes
  #-----------------------------------------------------------------------

  @staticmethod
  def get_type_attributes( obj, type_env ):

    obj_lst = [ _o for (name, _o) in obj.__dict__.iteritems()\
      if isinstance( name, basestring ) if not name.startswith( '_' )
    ]

    while obj_lst:
      o = obj_lst.pop()

      Type = BaseBehavioralRTLIRType.get_type( o )
      type_env[ freeze( o ) ] = Type

      # Make sure total_bits of struct is calculated correctly
      Type.type_str()

      try:
        type_env.update( Type.type_env )
      except:
        pass

#-------------------------------------------------------------------------
# Signal Type
#-------------------------------------------------------------------------
# Signal expressions are used for slicing, index, attribute, etc.

class Signal( BaseBehavioralRTLIRType ):
  def __init__( s, nbits, py_type = 'Wire' ):
    super( Signal, s ).__init__()
    s.nbits = nbits
    s.py_type = py_type

  def type_str( s ):
    ret = {
      'py_type'    : s.py_type,
      'nbits'      : s.nbits,
      'total_bits' : s.nbits,
      'n_dim_size' : [],
    }
    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return s.nbits == other.nbits

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Signal ) and s == obj:
      return True
    if isinstance( obj, Const ) and s.nbits == obj.nbits:
      return True
    return False

  @staticmethod
  def cast( obj ):
    """Cast `obj` into Signal object or NoneType() if failed"""
    if isinstance( obj, Signal ):
      return obj

    if isinstance( obj, Const ):
      return Signal( obj.nbits )

    assert False, "Cannot cast into temporary variables in L1"

  def __repr__( s ):
    return 'Signal'

#-------------------------------------------------------------------------
# Array Type
#-------------------------------------------------------------------------
# Packed array type. We assume all Python list translates to packed
# array because only packed structs are synthesizable.

class Array( BaseBehavioralRTLIRType ):
  def __init__( s, length, Type ):
    super( Array, s ).__init__()
    s.length = length
    s.Type = Type

  def type_str( s ):
    sub_type_str = s.Type.type_str()
    ret = {
      'py_type'    : sub_type_str[ 'py_type' ],
      'nbits'      : sub_type_str[ 'nbits' ],
      'total_bits' : 0,
      'n_dim_size' : [ s.length ] + sub_type_str[ 'n_dim_size' ]
    }

    total_vec_num = reduce( lambda x,y: x*y, ret['n_dim_size'], 1 )

    ret[ 'total_bits' ] = total_vec_num * ret[ 'nbits' ]

    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    if s.length == other.length and type( s.Type ) == type( other.Type ):
      if not isinstance( s.Type, Array ):
        return s.Type == other.Type
      else:
        return s.Type.__eq__( other.Type )
    else:
      return False

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Array ) and s.Type == obj.Type:
      return True
    return False

  def __repr__( s ):
    return 'Array'

#-------------------------------------------------------------------------
# Const Type
#-------------------------------------------------------------------------
# Constant expressions, used as slicing upper/lower bounds, index

class Const( BaseBehavioralRTLIRType ):
  def __init__( s, is_static, nbits, value = None ):
    # is_static == False <=> value == None
    s.is_static = is_static
    s.nbits = nbits
    s.value = value

  def type_str( s ):
    assert not s.value is None, "Trying to declare a constant but did not\
 provide initial value!"

    ret = {
      'py_type'    : 'Bits' + str(s.nbits),
      'value'      : str(s.value),
      'nbits'      : s.nbits,
      'total_bits' : s.nbits,
      'n_dim_size' : [],
    }

    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return ( s.is_static and other.is_static ) and ( s.nbits == other.nbits )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Const ) and s == obj:
      return True
    return False

  def __repr__( s ):
    return 'Const'

#-------------------------------------------------------------------------
# BaseAttr Type
#-------------------------------------------------------------------------
# This is the base type for all types that can serve as the base of an
# attribute operation.

class BaseAttr( BaseBehavioralRTLIRType ):
  def __init__( s, obj, type_env ):
    super( BaseAttr, s ).__init__()
    s.obj = obj
    s.type_env = type_env

  def type_str( s ):
    raise NotImplementedError

  def __eq__( s, other ):
    return is_obj_eq( s.type_env, other.type_env )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    raise NotImplementedError

  def __repr__( s ):
    raise NotImplementedError

#-------------------------------------------------------------------------
# Module Type
#-------------------------------------------------------------------------
# Any variable that refers to a module has this type.

class Module( BaseAttr ):
  def __init__( s, obj, type_env ):
    super( Module, s ).__init__( obj, type_env )

  def type_str( s ):
    ret = {
      'py_type'    : s.obj.__class__.__name__,
      'nbits'      : 0,
      'total_bits' : 0,
      'n_dim_size' : []
    }

    return ret

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Module ) and s == obj:
      return True
    return False

  def __repr__( s ):
    return 'Module'
