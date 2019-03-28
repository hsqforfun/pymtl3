#=========================================================================
# StructuralTranslatorL1.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 24, 2019

import inspect
from collections import defaultdict, deque

from pymtl import *

from pymtl.passes.utility import get_string, collect_objs

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata
from ..utility import is_BitsX

class StructuralTranslatorL1( BaseRTLIRTranslator ):

  def __init__( s, top ):

    super( StructuralTranslatorL1, s ).__init__( top )

    s.structural = TranslatorMetadata()

    s.hierarchy.component_srcs = []

    # Signal data type backend representations
    
    # Vector type
    s.hierarchy.bit_types = {}
    # Integer constant type without width specification
    s.hierarchy.int_type = None
    # Integer constant type with width specification
    s.hierarchy.int_fw_types = {}

    # Signal declarations

    s.structural.ports  = {}
    s.structural.wires  = {}
    s.structural.consts = {}

    # Signal connections

    s.structural.connections_self_self   = defaultdict(set)

    s.gen_structural_trans_l1_metadata( top )

  def translate_structural( s, m ):

    # Translate declarations of signals and constants

    s.structural.port_decls = {}
    s.translate_port_decls( s.top )

    s.structural.wire_decls = {}
    s.translate_wire_decls( s.top )

    s.structural.const_decls = {}
    s.translate_const_decls( s.top )

    # Translate connections

    s.translate_connections( m )

    # Generate the component backend representation

    s.translate_component( m )

  #-----------------------------------------------------------------------
  # translate_port_decls
  #-----------------------------------------------------------------------

  def translate_port_decls( s, m ):

    port_decls = []
    
    for name, port in s.structural.ports[m]:

      if   isinstance( port, InVPort ):  direction = 'input'
      elif isinstance( port, OutVPort ): direction = 'output'
      else:                              assert False

      port_decls.append( s.__class__.rtlir_tr_port_decl(
        direction, s.__class__.rtlir_tr_var_name( name ),
        s.dtype_tr_get_member_type( port )
      ) )

    s.component[m].port_decls = s.__class__.rtlir_tr_port_decls( port_decls )

  #-----------------------------------------------------------------------
  # translate_wire_decls
  #-----------------------------------------------------------------------

  def translate_wire_decls( s, m ):

    wire_decls = []
    
    for name, wire in s.structural.wires[m]:

      wire_decls.append( s.__class__.rtlir_tr_wire_decl(
        s.__class__.rtlir_tr_var_name( name ),
        s.dtype_tr_get_member_type( wire )
      ) )

    s.component[m].wire_decls = s.__class__.rtlir_tr_wire_decls( wire_decls )

  #-----------------------------------------------------------------------
  # translate_const_decls
  #-----------------------------------------------------------------------

  def translate_const_decls( s, m ):

    const_decls = []
    
    for name, const in s.structural.consts[m]:

      const_decls.append( s.__class__.rtlir_tr_const_decl(
        s.__class__.rtlir_tr_var_name( name ),
        s.dtype_tr_get_member_type( const ),
        const
      ) )

    s.component[m].const_decls = s.__class__.rtlir_tr_const_decls( const_decls )

  #-----------------------------------------------------------------------
  # translate_connections
  #-----------------------------------------------------------------------

  def translate_connections( s, m ):

    m_connections = set()
    m_connections |= ( s.structural.connections_self_self[m] )

    connections   = []
    connect_order = m.get_connect_order()

    ordered_conns   = [ '' for x in xrange(len(connect_order)) ]
    unordered_conns = []

    # Generate an ordered list of connections
    for writer, reader in m_connections:

      if StructuralTranslatorL1.is_in_list( (writer, reader), connect_order ):
        pos = StructuralTranslatorL1.get_pos( (writer,reader), connect_order )
        ordered_conns[pos] = (writer, reader)

      else:
        unordered_conns.append( (writer, reader) )

    for writer, reader in ordered_conns + unordered_conns:
      connections.append( s.__class__.rtlir_tr_connection(
        s.dtype_tr_signal( writer, m ), s.dtype_tr_signal( reader, m )
      ) )

    s.component[m].connections =\
      s.__class__.rtlir_tr_connections( connections )

  #-----------------------------------------------------------------------
  # translate_component
  #-----------------------------------------------------------------------

  def translate_component( s, m ):

    s.component[m].component_name = s.gen_component_name( m )

    s.hierarchy.component_srcs.append(
      s.__class__.rtlir_tr_component( s.component[m] )
    )

  #-----------------------------------------------------------------------
  # get_model_parameters
  #-----------------------------------------------------------------------

  def get_component_parameters( s, m ):

    ret = {}

    kwargs = m._dsl.kwargs.copy()
    if "elaborate" in m._dsl.param_dict:
      kwargs.update(
        { x: y\
          for x, y in m._dsl.param_dict[ "elaborate" ].iteritems() if x 
      } )

    ret[ '' ] = m._dsl.args

    ret.update( kwargs )

    return ret

  #-----------------------------------------------------------------------
  # gen_module_name
  #-----------------------------------------------------------------------

  def gen_component_name( s, m ):

    ret = m.__class__.__name__

    param = s.get_component_parameters( m )

    argspec = inspect.getargspec( getattr( m, 'construct' ) )

    # Add const args to module name
    for idx, arg_name in enumerate( argspec.args[1:] ):
      arg_value = param[ '' ][idx]
      ret += '__' + arg_name + '_' + get_string(arg_value)

    # Add varargs to module name
    if len( param[''] ) > len( argspec.args[1:] ):
      ret += '__' + argspec.varargs
    
    for arg_value in param[''][ len(argspec.args[1:]): ]:
      ret += '___' + get_string(arg_value)

    # Add kwargs to module name
    for arg_name, arg_value in param.iteritems():
      if arg_name == '': continue
      ret += '__' + arg_name + '_' + get_string(arg_value)

    return ret

  #-----------------------------------------------------------------------
  # is_in_list
  #-----------------------------------------------------------------------

  @staticmethod
  def is_in_list( pair, List ):
    for u, v in List:
      if (u is pair[0] and v is pair[1]) or (u is pair[1] and v is pair[0]):
        return True
    return False

  #-----------------------------------------------------------------------
  # get_pos
  #-----------------------------------------------------------------------

  @staticmethod
  def get_pos( pair, List ):
    for idx, (u, v) in enumerate(List):
      if (u is pair[0] and v is pair[1]) or (u is pair[1] and v is pair[0]):
        return idx
    assert False

  #-----------------------------------------------------------------------
  # dtype_tr_get_member_type
  #-----------------------------------------------------------------------
  # This function returns the type string generated by the backend.

  def dtype_tr_get_member_type( s, obj ):

    try:

      # non-constant Signals

      Type = obj._dsl.Type

    except AttributeError:

      # Constant instances. Assume integer at L1.

      assert isinstance( obj, ( int, Bits ) ),\
        'non-integer constant attribute {} is not translatable!'.format(
            str( obj )
        )

      if isinstance( obj, int ):
        ret = s.__class__.rtlir_tr_const_int_type()
        s.hierarchy.int_type = ret
        return ret

      if isinstance( obj, Bits ):
        ret = s.__class__.rtlir_tr_const_int_fw_type( obj.nbits )
        s.hierarchy.int_fw_types[ obj.nbits ] = ret
        return ret

    if is_BitsX( Type ):
      ret = s.__class__.rtlir_tr_bit_type( Type.nbits )
      s.hierarchy.bit_types[ Type.__name__ ] = ret
      return ret

    else:
      assert False, 'unrecognized attribute type {}!'.format( str( Type ) )

  #-----------------------------------------------------------------------
  # dtype_tr_signal
  #-----------------------------------------------------------------------
  # This function returns the signal expression generated by the backend.

  def dtype_tr_signal( s, obj, m ):

    def is_singleton_slice( Slice ):

      if Slice is None: return False
      
      assert Slice.start != None and Slice.stop != None,\
        'the start and stop of a slice cannot be None!'

      return Slice.stop == Slice.start+1

    # L1: obj must be a signal that belongs to the current component. No
    # subcomponent is allowed at this level.

    Slice = obj._dsl.slice

    if not ( Slice is None ):

      # Bit slicing and bit indexing

      parent = obj._dsl.parent_obj

      if is_singleton_slice(parent._dsl.slice) and is_singleton_slice(Slice):

        # Slicing on a 1-bit is not supported by verilator

        return s.dtype_tr_signal( parent, m )

      return s.__class__.rtlir_tr_bit_slice(
        s.dtype_tr_signal( obj._dsl.parent_obj, m ),
        Slice.start, Slice.stop, Slice.step
      )

    elif ('level' in obj._dsl.__dict__):

      m_level = m._dsl.level
      obj_level = obj._dsl.level

      assert obj_level == (m_level+1),\
"Only attributes of the current component under translation are allowed at L1!"

      return s.__class__.rtlir_tr_var_name( obj._dsl.my_name )

    else:
      assert False,\
        'internal translation error: wild signal {} encountered!'.format(
            str( obj )
        )

  #-----------------------------------------------------------------------
  # gen_structural_trans_l1_metadata
  #-----------------------------------------------------------------------

  def gen_structural_trans_l1_metadata( s, m ):

    # Collect all members of m

    s.structural.ports[m]  = collect_objs( m, ( InVPort, OutVPort ) )
    s.structural.wires[m]  = collect_objs( m, Wire )
    s.structural.consts[m] = collect_objs( m, ( int, Bits ) )

    # Generate the connections assuming no sub-components

    nets = m.get_all_value_nets()
    adjs = m.get_signal_adjacency_dict()

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
              s.structural.\
                connections_self_self[ writer_host ].add( ( u, v ) )

            else: assert False, "No sub-components are allowed at L1!"

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_const_int_type():
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_const_int_fw_type( nbits ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_bit_type( nbits ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_bit_slice( base_signal, start, stop, step ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_port_decls( port_decls ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_port_decl( direction, name, Type ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_wire_decls( wire_decls ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_wire_decl( name, Type ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_const_decls( const_decls ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_const_decl( name, Type, value ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_connections( connections ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_connection( wr_signal, rd_signal ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_component( component_nspace ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_var_name( var_name ):
    raise NotImplementedError()
