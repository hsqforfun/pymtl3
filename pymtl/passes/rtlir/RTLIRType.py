#=========================================================================
# RTLIRType.py
#=========================================================================
# This file contains the definitions of RTLIR types, which is
# independent from the PyMTL functionalities. Function `gen_rtlir_inst`
# takes a python object and returns its RTLIR representation.
#
# Author : Peitian Pan
# Date   : March 31, 2019

import inspect, copy, pymtl

from utility import collect_objs
from RTLIRDataType import *

#-------------------------------------------------------------------------
# BaseRTLIRType
#-------------------------------------------------------------------------

class BaseRTLIRType( object ):

  def __new__( cls, *args, **kwargs ):

    return super( BaseRTLIRType, cls ).__new__( cls )

  def __init__( s ):

    super( BaseRTLIRType, s ).__init__()

  def __ne__( s, other ): return not s.__eq__( other )

#-------------------------------------------------------------------------
# is_of_type
#-------------------------------------------------------------------------

def is_of_type( obj, Type ):

  assert issubclass( Type, BaseRTLIRType )

  if isinstance( obj, Type ): return True

  if isinstance( obj, Array ) and isinstance( obj.get_sub_type(), Type ):

    return True

  return False

#-------------------------------------------------------------------------
# NoneType
#-------------------------------------------------------------------------
# This type is used when a TmpVar node is visited before getting its type
# from an assignment.

class NoneType( BaseRTLIRType ):

  def __init__( s ):

    super( NoneType, s ).__init__()

  def __eq__( s, other ): return type( s ) == type( other )

#-------------------------------------------------------------------------
# Array
#-------------------------------------------------------------------------
# An unpacked array type

class Array( BaseRTLIRType ):

  def __init__( s, dim_sizes, sub_type, unpacked = False ):

    assert isinstance( sub_type, BaseRTLIRType )
    assert not isinstance( sub_type, Array )
    assert len( dim_sizes ) >= 1
    assert reduce( lambda s, i: s+i, dim_sizes, 0 ) > 0

    super( Array, s ).__init__()
    s.dim_sizes = dim_sizes
    s.sub_type = sub_type
    s.unpacked = unpacked

  def _is_unpacked( s ): return s.unpacked

  def __eq__( s, other ):

    if type( s ) != type( other ): return False
    if s.dim_sizes != other.dim_sizes: return False
    return s.sub_type == other.sub_type

  def get_next_dim_type( s ):

    if len( s.dim_sizes ) == 1: return copy.copy( s.sub_type )

    _s = copy.copy( s )
    _s.dim_sizes = s.dim_sizes[1:]
    return _s

    # return Array( s.dim_sizes[1:], s.sub_type )

  def get_dim_sizes( s ): return s.dim_sizes

  def get_sub_type( s ): return s.sub_type

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""

    return s.__eq__( obj )

  def __str__( s ):

    return 'Array'

#-------------------------------------------------------------------------
# Signal
#-------------------------------------------------------------------------

class Signal( BaseRTLIRType ):

  def __init__( s, dtype, unpacked = False ):

    assert isinstance( dtype, BaseRTLIRDataType )

    super( Signal, s ).__init__()
    s.dtype = dtype
    s.unpacked = unpacked

  def __eq__( s, other ):

    if type( s ) != type( other ): return False
    return s.dtype == other.dtype

  def __ne__( s, other ): return not s.__eq__( other )

  def is_packed_indexable( s ): return isinstance( s.dtype, PackedArray )

  def get_dtype( s ): return s.dtype

  def _is_unpacked( s ): return s.unpacked

#-------------------------------------------------------------------------
# Port
#-------------------------------------------------------------------------

class Port( Signal ):

  def __init__( s, direction, dtype, unpacked = False ):
    
    super( Port, s ).__init__( dtype, unpacked )
    s.direction = direction

  def __eq__( s, other ):

    return super( Port, s ).__eq__( other ) and s.direction == other.direction

  def get_direction( s ): return s.direction

  def get_next_dim_type( s ):

    assert s.is_packed_indexable()
    return Port( s.direction, s.dtype.get_next_dim_type(), s.unpacked )

#-------------------------------------------------------------------------
# Wire
#-------------------------------------------------------------------------

class Wire( Signal ):

  def __init__( s, dtype, unpacked = False ):

    super( Wire, s ).__init__( dtype, unpacked )

  def get_next_dim_type( s ):

    assert s.is_packed_indexable()
    return Wire( s.dtype.get_next_dim_type(), s.unpacked )

#-------------------------------------------------------------------------
# Const
#-------------------------------------------------------------------------
# Constant instances of PyMTL components

class Const( Signal ):

  def __init__( s, dtype, unpacked = False ):

    super( Const, s ).__init__( dtype, unpacked )

  def get_next_dim_type( s ):

    assert s.is_packed_indexable()
    return Const( s.dtype.get_next_dim_type(), s.unpacked )

#-------------------------------------------------------------------------
# Interface
#-------------------------------------------------------------------------

class Interface( BaseRTLIRType ):

  def __init__( s, name, views = [] ):

    super( Interface, s ).__init__()
    assert s._check_views( views ),\
        '{} does not belong to interface {}!'.format( views, name )
    s.name = name
    s.views = views
    s.properties = s._gen_properties( views )

  # Private methods

  def _set_name( s, name ): s.name = name

  def _gen_properties( s, views ):

    _properties = {}

    for view in views:

      assert isinstance( view, InterfaceView )

      for id_, rtype in view.get_all_ports_packed():

        if isinstance( rtype, Array ):

          _properties[ id_ ] = Array( rtype.get_dim_sizes(),
            Wire( rtype.get_subcomps().get_dtype() ), rtype.unpacked )

        else:

          _properties[ id_ ] = Wire( rtype.get_dtype(), rtype.unpacked )

    return _properties

  def _check_views( s, views ):

    _properties = s._gen_properties( views )

    for view in views:

      assert isinstance( view, InterfaceView )
      props = view.get_all_ports()

      if len( props ) != len( _properties.keys() ):

        return False

      for prop_id, prop_rtype in props:

        if not prop_id in _properties: return False
        if Wire(prop_rtype.get_dtype()) != _properties[prop_id]: return False

    return True

  # Public APIs

  def get_name( s ): return s.name

  def get_all_views( s ): return s.views

  def get_all_wires( s ):

    return filter(
      lambda ( name, wire ): isinstance( wire, Wire ),
      s.properties.iteritems()
    )

  def get_all_wires_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Wire ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Wire )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def can_add_view( s, view ): return s._check_views( s.views + [ view ] )

  def add_view( s, view ):

    if s.can_add_view( view ):

      s.views.append( view )
      s.properties = s._gen_properties( s.views )

#-------------------------------------------------------------------------
# InterfaceView
#-------------------------------------------------------------------------

class InterfaceView( BaseRTLIRType ):

  def __init__( s, name, properties, unpacked = False ):

    super( InterfaceView, s ).__init__()
    s.name = name
    s.interface = None
    s.properties = properties
    s.unpacked = unpacked

    # Sanity check

    for name, rtype in properties.iteritems():

      assert isinstance( name, str ) and is_of_type( rtype, Port )

  # Private methods

  def _set_interface( s, interface ): s.interface = interface

  def _is_unpacked( s ): return s.unpacked

  # Public APIs

  def __eq__( s, other ):

    return type(s) == type(other) and s.name == other.name

  def get_name( s ): return s.name

  def get_interface( s ):

    if s.interface is None:
      
      assert False, 'internal error: {} has no interface!'.format( s )
    
    return s.interface

  def get_input_ports( s ):

    return filter(
      lambda ( id_, port ): port.direction == 'input',
      s.properties.iteritems()
    )

  def get_output_ports( s ):

    return filter(
      lambda ( id_, port ): port.direction == 'output',
      s.properties.iteritems()
    )

  def has_property( s, p ): return p in s.properties

  def get_property( s, p ): return s.properties[ p ]

  def get_all_ports( s ):

    return filter(
      lambda ( name, port ): isinstance( port, Port ),
      s.properties.iteritems()
    )

  def get_all_ports_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Port ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Port )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

#-------------------------------------------------------------------------
# Component
#-------------------------------------------------------------------------

class Component( BaseRTLIRType ):

  def __init__( s, obj, properties, unpacked = False ):

    super( Component, s ).__init__()

    s.name = obj.__class__.__name__
    s.argspec = inspect.getargspec( getattr( obj, 'construct' ) )
    s.params = s._gen_parameters( obj )
    s.properties = properties
    s.unpacked = unpacked

  # Private methods
  
  def _gen_parameters( s, obj ):

    defaults = s.argspec.defaults if s.argspec.defaults else ()

    # The non-keyword parameters are indexed by an empty string
    ret = { '' : obj._dsl.args }
    default_len = len(s.argspec.args[1:])-len(ret[''])
    assert default_len <= len( defaults ),\
      'varargs are not allowed at construct() of {}!'.format( obj )
    if not default_len == 0:
      ret[''] = ret[''] + defaults[-default_len:]

    kwargs = obj._dsl.kwargs.copy()

    if 'elaborate' in obj._dsl.param_dict:

      kwargs.update( {
        x:y for x, y in obj._dsl.param_dict['elaborate'].iteritems() if x
      } )

    ret.update( kwargs )

    return ret

  def _is_unpacked( s ): return s.unpacked

  # Public APIs

  def __eq__( s, other ):

    if type( s ) != type( other ): return False
    if s.name != other.name or s.params != other.params: return False
    return True

  def get_name( s ): return s.name

  def get_params( s ): return s.params

  def get_argspec( s ): return s.argspec

  def get_ports( s ):

    return filter(
      lambda ( id_, port ): isinstance( port, Port ),
      s.properties.iteritems()
    )

  def get_ports_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Port ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Port )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_wires( s ):

    return filter(
      lambda ( id_, wire ): isinstance( wire, Wire ),
      s.properties.iteritems()
    )

  def get_wires_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Wire ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Wire )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_consts( s ):

    return filter(
      lambda ( id_, const ): isinstance( const, Const ),
      s.properties.iteritems()
    )

  def get_consts_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Const ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Const )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_ifc_views( s ):

    return filter(
      lambda ( id_, ifc ): isinstance( ifc, InterfaceView ),
      s.properties.iteritems()
    )

  def get_ifc_views_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, InterfaceView ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(),InterfaceView )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_ifcs( s ):

    return filter(
      lambda ( id_, ifc ): isinstance( ifc, Interface ),
      s.properties.iteritems()
    )

  def get_subcomps( s ):

    return filter(
      lambda ( id_, subcomp ): isinstance( subcomp, Component ),
      s.properties.iteritems()
    )

  def get_subcomps_packed( s ):

    return filter(
      lambda ( id_, t ):\
        ( isinstance( t, Component ) and not t._is_unpacked() ) or\
        ( isinstance( t, Array ) and isinstance( t.get_sub_type(), Component )\
          and not t._is_unpacked() ),
      s.properties.iteritems()
    )

  def has_property( s, p ): return p in s.properties

  def get_property( s, p ): return s.properties[ p ]

  def get_all_properties( s ): return s.properties

#-------------------------------------------------------------------------
# can_convert_to_rtlir
#-------------------------------------------------------------------------

def can_convert_to_rtlir( obj ):

  pymtl_constructs = (
    pymtl.InPort, pymtl.OutPort, pymtl.Wire, pymtl.Bits, pymtl.Interface,
    pymtl.Component
  )

  if isinstance( obj, list ):
    while isinstance( obj, list ):
      assert len( obj ) > 0
      obj = obj[0]
    return can_convert_to_rtlir( obj )

  elif isinstance( obj, pymtl_constructs ):
    return True

  elif isinstance( obj, int ):
    return True
  
  else: return False

#-------------------------------------------------------------------------
# get_rtlir
#-------------------------------------------------------------------------
# generate the RTLIR instance of the given object

def get_rtlir( obj ):

  def can_convert_to_ifc_rtlir( obj ):

    pymtl_ports = ( pymtl.InPort, pymtl.OutPort )

    if isinstance( obj, list ):
      while isinstance( obj, list ):
        assert len( obj ) > 0
        obj = obj[0]
      return can_convert_to_ifc_rtlir( obj )

    elif isinstance( obj, pymtl_ports ): return True

    else: return False

  def unpack( id_, Type ):

    if not isinstance( Type, Array ): return [ ( id_, Type ) ]

    ret = []

    for idx in xrange( Type.get_dim_sizes()[0] ):

      ret.append( ( id_+'[{}]'.format(idx), Type.get_next_dim_type() ) )
      ret.extend(unpack(id_+'[{}]'.format( idx ), Type.get_next_dim_type()))

    return ret

  def add_packed_instances( id_, Type, properties ):
    """
       Unpack `Type` instance and add all elements into `properties`.
       Note that the elements inserted into `properties` can be another
       Array instance!
    """

    assert isinstance( Type, Array )

    for _id, _Type in unpack( id_, Type ):

      assert hasattr( _Type, 'unpacked' )
      _Type.unpacked = True
      properties[ _id ] = _Type

  # A list of instances
  if isinstance( obj, list ):

    assert len( obj ) > 0
    ref_type = get_rtlir( obj[0] )
    assert\
      reduce( lambda res,i: res and (get_rtlir(i)==ref_type),obj ),\
      'all elements of array {} must have the same type {}!'.format(
        obj, ref_type )
    dim_sizes = []

    while isinstance( obj, list ):

      assert len( obj ) > 0
      dim_sizes.append( len( obj ) )
      obj = obj[0]

    return Array( dim_sizes, get_rtlir( obj ) )

  # A Port instance
  elif isinstance( obj, ( pymtl.InPort, pymtl.OutPort ) ):

    if isinstance( obj, pymtl.InPort ):

      return Port( 'input', get_rtlir_dtype( obj ) )

    elif isinstance( obj, pymtl.OutPort ):

      return Port( 'output', get_rtlir_dtype( obj ) )

    else: assert False

  # A Wire instance
  elif isinstance( obj, pymtl.Wire ):

    return Wire( get_rtlir_dtype( obj ) )

  # A Constant instance
  elif isinstance( obj, ( int, pymtl.Bits ) ):

    return Const( get_rtlir_dtype( obj ) )

  # An Interface view instance
  elif isinstance( obj, pymtl.Interface ):

    properties = {}

    for _id, _obj in collect_objs( obj, object, True ):

      if not can_convert_to_ifc_rtlir( _obj ): continue

      _obj_type = get_rtlir( _obj )
      properties[ _id ] = _obj_type

      if not is_of_type( _obj_type, ( Port ) ):

        assert False,\
          "RTLIR Interface type can only include Port objects!"

      if isinstance( _obj_type, Array ):

        add_packed_instances( _id, _obj_type, properties )

    return InterfaceView( obj.__class__.__name__, properties )

  # A Component instance
  elif isinstance( obj, pymtl.Component ):

    # Collect all attributes of `obj`

    properties = {}

    for _id, _obj in collect_objs( obj, object, True ):

      # Untranslatable attributes will be ignored
      if not can_convert_to_rtlir( _obj ): continue

      _obj_type = get_rtlir( _obj )
      properties[ _id ] = _obj_type

      if isinstance( _obj_type, Array ):
        
        add_packed_instances( _id, _obj_type, properties )
    
    return Component( obj, properties )

  # Cannot convert `obj` into RTLIR representation

  else:

    assert False, 'cannot convert {} into RTLIR!'.format( obj )
