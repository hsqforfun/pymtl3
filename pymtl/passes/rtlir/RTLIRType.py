#=========================================================================
# RTLIRType.py
#=========================================================================
# This file contains the definitions of RTLIR types, which is
# independent from the PyMTL functionalities. Function `gen_rtlir_inst`
# takes a python object and returns its RTLIR representation.
#
# Author : Peitian Pan
# Date   : March 31, 2019

import inspect, pymtl

from pymtl.passes.utility import *

from RTLIRDataType import *

#-------------------------------------------------------------------------
# BaseRTLIRType
#-------------------------------------------------------------------------

class BaseRTLIRType( object ):

  def __new__( cls, *args, **kwargs ):

    return super( BaseRTLIRType, cls ).__new__( cls )

  def __init__( s ):

    super( BaseRTLIRType, s ).__init__()

#-------------------------------------------------------------------------
# NoneType
#-------------------------------------------------------------------------
# This type is used when a TmpVar node is visited before getting its type
# from an assignment.

class NoneType( BaseRTLIRType ):

  def __init__( s ):

    super( NoneType, s ).__init__()

#-------------------------------------------------------------------------
# Signal
#-------------------------------------------------------------------------

class Signal( BaseRTLIRType ):

  def __init__( s, dtype ):

    assert isinstance( dtype, BaseRTLIRDataType )

    super( Signal, s ).__init__()
    s.dtype = dtype

  def get_dtype( s ):

    return s.dtype

#-------------------------------------------------------------------------
# Port
#-------------------------------------------------------------------------

class Port( Signal ):

  def __init__( s, direction, dtype ):
    
    super( Port, s ).__init__( dtype )
    s.direction = direction

  def get_direction( s ):

    return s.direction

#-------------------------------------------------------------------------
# Wire
#-------------------------------------------------------------------------

class Wire( Signal ):

  def __init__( s, dtype ):

    super( Wire, s ).__init__( dtype )

  def __eq__( s, other ):

    if not isinstance( other, Wire ): return False
    return s.get_dtype() == other.get_dtype()

  def __ne__( s, other ):

    return not s.__eq__( other )

#-------------------------------------------------------------------------
# Const
#-------------------------------------------------------------------------
# Constant instances of PyMTL components

class Const( Signal ):

  def __init__( s, dtype ):

    super( Const, s ).__init__( dtype )

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

  def _set_name( s, name ):

    s.name = name

  def _gen_properties( s, views ):

    _properties = {}

    for view in views:

      assert isinstance( view, InterfaceView )

      for name, rtype in view.get_all_properties().iteritems():

        _properties[ name ] = Wire( rtype.get_dtype() )

    return _properties

  def _check_views( s, views ):

    _properties = s._gen_properties( views )

    for view in views:

      assert isinstance( view, InterfaceView )
      props = view.get_all_properties()

      if len( props.keys() ) != len( _properties.keys() ):

        return False

      for prop_name, prop_rtype in props.iteritems():

        if not prop_name in props: return False
        if Wire( prop_rtype.get_dtype() ) != _properties[ prop_name ]: return False

    return True

  # Public APIs

  def get_name( s ):

    return s.name

  def get_all_views( s ):

    return s.views

  def get_all_properties( s ):

    return s.properties

  def can_add_view( s, view ):

    _views = s.views + [ view ]
    return s._check_views( _views )

  def add_view( s, view ):

    if s.can_add_view( view ):

      s.views.append( view )
      s.properties = s._gen_properties( s.views )

#-------------------------------------------------------------------------
# InterfaceView
#-------------------------------------------------------------------------

class InterfaceView( BaseRTLIRType ):

  def __init__( s, name, properties ):

    super( InterfaceView, s ).__init__()
    s.name = name
    s.interface = None
    s.properties = properties

    # Sanity check

    for name, rtype in properties.iteritems():

      assert isinstance( name, str ) and isinstance( rtype, Port )

  # Private methods

  def _set_interface( s, interface ):

    s.interface = interface

  # Public APIs

  def __eq__( s, other ):

    return (type(s) == type(other)) and (s.name == other.name)

  def get_name( s ):

    return s.name

  def get_interface( s ):

    if s.interface is None:
      
      assert False, 'internal error: {} has no interface name!'.format( s )
    
    return s.interface

  def get_input_ports( s ):

    return filter(
      lambda ( name, port ): port.direction == 'input',
      s.properties.iteritems()
    )

  def get_output_ports( s ):

    return filter(
      lambda ( name, port ): port.direction == 'output',
      s.properties.iteritems()
    )

  def has_property( s, p ):

    return p in s.properties

  def get_property( s, p ):

    return s.properties[ p ]

  def get_all_properties( s ):

    return s.properties

#-------------------------------------------------------------------------
# Component
#-------------------------------------------------------------------------

class Component( BaseRTLIRType ):

  def __init__( s, properties ):

    super( Component, s ).__init__()

    s.properties = properties

  def get_ports( s ):

    return filter(
      lambda ( name, port ): isinstance( port, Port ),
      s.properties.iteritems()
    )

  def get_wires( s ):

    return filter(
      lambda ( name, wire ): isinstance( wire, Wire ),
      s.properties.iteritems()
    )

  def get_consts( s ):

    return filter(
      lambda ( name, const ): isinstance( const, Const ),
      s.properties.iteritems()
    )

  def get_ifc_views( s ):

    return filter(
      lambda ( name, ifc ): isinstance( ifc, InterfaceView ),
      s.properties.iteritems()
    )

  def get_ifcs( s ):

    return filter(
      lambda ( name, ifc ): isinstance( ifc, Interface ),
      s.properties.iteritems()
    )

  def get_subcomps( s ):

    return filter(
      lambda ( name, subcomp ): isinstance( subcomp, Component ),
      s.properties.iteritems()
    )

  def has_property( s, p ):

    return p in s.properties

  def get_property( s, p ):

    return s.properties[ p ]

  def get_all_properties( s ):

    return s.properties

#-------------------------------------------------------------------------
# get_rtlir_type
#-------------------------------------------------------------------------
# generate the RTLIR instance of the given object

def get_rtlir_type( obj ):

  def unpack( name, List ):

    if not isinstance( List, list ):

      return [ ( name, List ) ]

    assert len( List ) > 0

    ret = []

    for idx, element in enumerate( List ):

      ret.extend( unpack( name+'[{}]'.format( idx ), element ) )

    return ret

  def add_packed_instances( name, obj, Type, properties ):

    if isinstance( obj, Type ) and isinstance( obj, list ):

      for _name, _obj in unpack( name, obj ):

        properties[ _name ] = get_rtlir_type( _obj )

      return True

    else: return False

  # Port instances

  if is_of_type( obj, ( pymtl.InVPort, pymtl.OutVPort ) ):

    if is_of_type( obj, pymtl.InVPort ):

      return Port( 'input', get_rtlir_dtype( obj ) )

    elif is_of_type( obj, pymtl.OutVPort ):

      return Port( 'output', get_rtlir_dtype( obj ) )

    else: assert False

  # Wire instances

  elif is_of_type( obj, pymtl.Wire ):

    return Wire( get_rtlir_dtype( obj ) )

  # Constant instances

  elif is_of_type( obj, ( int, pymtl.Bits ) ):

    if isinstance( obj, list ):

      assert False, 'internal error: constants should be unpacked!'

    return Const( get_rtlir_dtype( obj ) )

  # Interface view instances

  elif is_of_type( obj, pymtl.Interface ):

    if isinstance( obj, list ):

      assert False, 'internal error: interface views should be unpacked!'

    # Handle a single interface

    properties = {}

    for _name, _obj in collect_objs( obj, object, True ):

      # if add_packed_instances(_name, _obj, pymtl.Interface, properties):

         # continue

      _obj_type = get_rtlir_type( _obj )

      if not is_of_type( _obj_type, ( Port ) ):

        assert False,\
          "RTLIR Interface type can only include Port objects!"

      properties[ _name ] = _obj_type

    return InterfaceView( obj.__class__.__name__, properties )

  # Component instances

  elif is_of_type( obj, pymtl.RTLComponent ):

    if isinstance( obj, list ):

      assert False, 'internal error: components should be unpacked!'

    # Collect all attributes of `obj`

    properties = {}

    for _name, _obj in collect_objs( obj, object, True ):

      if add_packed_instances(_name, _obj, pymtl.RTLComponent, properties)\
       | add_packed_instances(_name, _obj, (int, pymtl.Bits), properties)\
       | add_packed_instances(_name, _obj, pymtl.Interface, properties):

         continue

      _obj_type = get_rtlir_type( _obj )

      properties[ _name ] = _obj_type
    
    return Component( properties )

  # Cannot convert `obj` into RTLIR representation

  else:

    assert False, 'cannot convert {} into RTLIR!'.format( obj )
