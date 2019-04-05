#=========================================================================
# StructuralTranslatorL1.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 24, 2019

import inspect, pymtl

from collections import defaultdict, deque

from pymtl.passes.utility import *
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL1Pass\
    import StructuralRTLIRGenL1Pass

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata

class StructuralTranslatorL1( BaseRTLIRTranslator ):

  def __init__( s, top ):

    super( StructuralTranslatorL1, s ).__init__( top )

    s.structural = TranslatorMetadata()

    # Component metadata

    s.structural.component_name  = {}
    s.structural.component_param = {}
    s.structural.component_argspec = {}

    # Declarations

    s.structural.decl_type_vector = []
    s.structural.decl_type_array  = []

    s.structural.decl_ports  = {}
    s.structural.decl_wires  = {}
    s.structural.decl_consts = {}

    # Connections

    s.structural.connections = {}

    # Generate metadata

    s.gen_structural_trans_metadata( top )

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  def gen_structural_trans_metadata( s, top ):

    top.apply( StructuralRTLIRGenL1Pass() )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------
  # This function will only be called once during the whole translation
  # process.

  def translate_structural( s, top ):

    s._translate_structural( top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------
  # This function will be recursively applied to differnet components in
  # the hierarchy.

  def _translate_structural( s, m ):

    s.structural.component_name[m] = m.__class__.__name__
    s.structural.component_param[m] = s.get_component_parameters( m )
    s.structural.component_argspec[m] = \
        inspect.getargspec( getattr( m, 'construct' ) )

    # Translate declarations of signals

    s.translate_decls( m )

    # Translate connections

    s.translate_connections( m )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  def translate_decls( s, m ):

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Ports

    port_decls = []

    for port_name, rtype in m_rtype.get_ports():

      port_decls.append(
        s.rtlir_tr_port_decl(
          s.rtlir_tr_var_name( port_name ),
          rtype,
          s.rtlir_data_type_translation( m, rtype.get_dtype() )
      ) )

    s.structural.decl_ports[m] = s.rtlir_tr_port_decls( port_decls )

    # Wires

    wire_decls = []

    for wire_name, rtype in m_rtype.get_wires():

      wire_decls.append(
        s.rtlir_tr_wire_decl(
          s.rtlir_tr_var_name( wire_name ),
          rtype,
          s.rtlir_data_type_translation( m, rtype.get_dtype() )
      ) )

    s.structural.decl_wires[m] = s.rtlir_tr_wire_decls( wire_decls )

    # Consts

    const_decls = []

    for const_name, rtype, instance in m._pass_structural_rtlir_gen.consts:

      const_decls.append(
        s.rtlir_tr_const_decl(
          s.rtlir_tr_var_name( const_name ),
          rtype,
          s.rtlir_data_type_translation( m, rtype.get_dtype() ),
          instance
      ) )

    s.structural.decl_consts[m] = s.rtlir_tr_const_decls( const_decls )

  #-----------------------------------------------------------------------
  # translate_connections
  #-----------------------------------------------------------------------

  def translate_connections( s, m ):

    connections = []
    _connections = m._pass_structural_rtlir_gen.connections

    for writer, reader in _connections:

      connections.append( s.rtlir_tr_connection(
        s.rtlir_signal_translation( writer, m ),
        s.rtlir_signal_translation( reader, m )
      ) )

    s.structural.connections[m] = s.rtlir_tr_connections( connections )

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
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------
  # Translate an RTLIR data type into its backend representation.

  def rtlir_data_type_translation( s, m, dtype ):

    if isinstance( dtype, Vector ):

      ret = s.rtlir_tr_vector_dtype( dtype )

      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_vector, True ):

        s.structural.decl_type_vector.append( ( dtype, ret ) )

      return ret

    elif isinstance( dtype, Array ):

      subtype = dtype.get_sub_dtype()

      assert isinstance( subtype, Vector ),\
          'Only vector type is supported at L1!'

      ret = s.rtlir_tr_vector_dtype( subtype )

      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_vector, True ):

        s.structural.decl_type_vector.append( ( subtype, ret ) )

      ret = s.rtlir_tr_array_dtype( dtype, ret )

      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_array, True ):

        s.structural.decl_type_array.append( ( dtype, ret ) )

      return ret

    else: assert False, "unsupported RTLIR dtype {} at L1!".format( dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_translation
  #-----------------------------------------------------------------------
  # Translate a PyMTL dsl signal object into its backend representation.

  def rtlir_signal_translation( s, obj, m ):

    def is_slicing( signal ):

      if isinstance( signal, pymtl.dsl.Signal ):

        Slice = signal._dsl.slice

        if Slice is None: return False

        assert Slice.start != None and Slice.stop != None,\
            'the start and stop of a slice cannot be None!'

        return True

      else: return False

    # L1: obj must be a signal that belongs to the current component. No
    # subcomponent is allowed at this level.
    # `obj` here should be a PyMTL Connectable instance

    # Signal ( Port, Wire ) connectable

    if isinstance( obj, pymtl.dsl.Signal ):

      Slice = obj._dsl.slice

      # Bit selection or part selection

      if is_slicing( obj ):

        if is_slicing( obj._dsl.parent_obj ):

          assert False,\
            'slicing {} over sliced signal {} is not allowed!'.format(
                Slice, obj._dsl.parent_obj
            )

        if Slice.stop == Slice.start + 1:

          return s.rtlir_tr_bit_selection(
            s.rtlir_signal_translation( obj._dsl.parent_obj, m ),
            Slice.start
          )

        else:

          return s.rtlir_tr_part_selection(
            s.rtlir_signal_translation( obj._dsl.parent_obj, m ),
            Slice.start, Slice.stop, Slice.step
          )

      # Use the signal itself

      elif ( 'level' in obj._dsl.__dict__ ):

        m_level = m._dsl.level
        obj_level = obj._dsl.level

        assert obj_level == (m_level+1),\
"Only attributes of the current component under translation are allowed at L1!"

        return s.rtlir_tr_var_name( obj._dsl.my_name )

      # No other signal oeprations are supported

      else:

        assert False,\
          'signal {} cannot be translated at L1!'.format( obj )

    # Const connectable

    elif isinstance( obj, pymtl.dsl.Const ):

      assert is_BitsX( obj._dsl.Type ), 'only vector type is supported at L1!'

      return s.rtlir_tr_literal_number(
        obj._dsl.const, obj._dsl.Type.nbits
      )

    # Other connectables are not supported at L1

    else: assert False, '{} connectable is not supported at L1!'.format( obj )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types

  def rtlir_tr_vector_dtype( s, Type ):
    raise NotImplementedError()

  def rtlir_tr_array_dtype( s, Type, subtype ):
    raise NotImplementedError()

  # Declarations

  def rtlir_tr_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_port_decl( s, name, Type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_wire_decls( s, wire_decls ):
    raise NotImplementedError()

  def rtlir_tr_wire_decl( s, name, Type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_const_decls( s, const_decls ):
    raise NotImplementedError()

  def rtlir_tr_const_decl( s, name, Type, dtype, value ):
    raise NotImplementedError()

  # Connections

  def rtlir_tr_connections( s, connections ):
    raise NotImplementedError()

  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_bit_selection( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_part_selection( s, base_signal, start, stop, step ):
    raise NotImplementedError()

  # Miscs

  def rtlir_tr_var_name( s, var_name ):
    raise NotImplementedError()

  def rtlir_tr_literal_number( s, value, nbits ):
    raise NotImplementedError()
