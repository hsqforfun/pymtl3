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
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr\
    import *

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata

class StructuralTranslatorL1( BaseRTLIRTranslator ):

  def __init__( s, top ):

    super( StructuralTranslatorL1, s ).__init__( top )

    s.structural = TranslatorMetadata()

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

    # Component metadata

    s.structural.component_unique_name = {}

    # Declarations

    s.structural.decl_type_vector = []
    s.structural.decl_type_array  = []

    s.structural.decl_ports  = {}
    s.structural.decl_wires  = {}
    s.structural.decl_consts = {}

    # Connections

    s.structural.connections = {}

    s._translate_structural( top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------
  # This function will be recursively applied to differnet components in
  # the hierarchy.

  def _translate_structural( s, m ):

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    s.structural.component_unique_name[m] =\
        s.rtlir_tr_component_unique_name(m_rtype)

    # Collect the metadata of the component so we can generate its name
    # later

    # s.structural.component_name[m] = m_rtype.get_name()
    # s.structural.component_params[m] = m_rtype.get_params()
    # s.structural.component_argspec[m] = m_rtype.get_argspec()

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

    for port_id, rtype in m_rtype.get_ports_packed():

      if isinstance( rtype, Array ):
        array_type = rtype
        port_rtype = rtype.get_sub_type()
      else:
        array_type = None
        port_rtype = rtype

      port_decls.append(
        s.rtlir_tr_port_decl(
          s.rtlir_tr_var_id( port_id ),
          port_rtype,
          s.rtlir_tr_unpacked_array_type( array_type ),
          s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
      ) )

    s.structural.decl_ports[m] = s.rtlir_tr_port_decls( port_decls )

    # Wires

    wire_decls = []

    for wire_id, rtype in m_rtype.get_wires_packed():

      if isinstance( rtype, Array ):
        array_type = rtype
        wire_rtype = rtype.get_sub_type()
      else:
        array_type = None
        wire_rtype = rtype

      wire_decls.append(
        s.rtlir_tr_wire_decl(
          s.rtlir_tr_var_id( wire_id ),
          wire_rtype,
          s.rtlir_tr_unpacked_array_type( array_type ),
          s.rtlir_data_type_translation( m, wire_rtype.get_dtype() )
      ) )

    s.structural.decl_wires[m] = s.rtlir_tr_wire_decls( wire_decls )

    # Consts

    const_decls = []

    for const_id, rtype, instance in m._pass_structural_rtlir_gen.consts:

      if isinstance( rtype, Array ):
        array_type = rtype
        const_rtype = rtype.get_sub_type()
      else:
        array_type = None
        const_rtype = rtype

      const_decls.append(
        s.rtlir_tr_const_decl(
          s.rtlir_tr_var_id( const_id ),
          const_rtype,
          s.rtlir_tr_unpacked_array_type( array_type ),
          s.rtlir_data_type_translation( m, const_rtype.get_dtype() ),
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
        s.rtlir_signal_expr_translation( writer, m ),
        s.rtlir_signal_expr_translation( reader, m )
      ) )

    s.structural.connections[m] = s.rtlir_tr_connections( connections )

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

    else: assert False, "unsupported RTLIR dtype {} at L1!".format( dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------
  # Translate a signal expression in RTLIR into its backend representation.
  # Only the following operations are supported at L1:
  # CurComp, CurCompAttr, BitSelection, PartSelection, PortIndex,
  # WireIndex, ConstIndex

  def rtlir_signal_expr_translation( s, expr, m ):

    if isinstance( expr, CurComp ):

      comp_id, comp_rtype = expr.get_component_id(), expr.get_rtype()
      return s.rtlir_tr_current_comp( comp_id, comp_rtype )

    elif isinstance( expr, CurCompAttr ):

      return s.rtlir_tr_current_comp_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr() )

    elif isinstance( expr, PortIndex ):

      return s.rtlir_tr_port_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, WireIndex ):

      return s.rtlir_tr_wire_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, ConstIndex ):

      return s.rtlir_tr_const_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    elif isinstance( expr, BitSelection ):

      base = expr.get_base()
      if isinstance( base, (PartSelection, BitSelection) ):
        assert False,\
          'bit selection {} over bit/part selection {} is not allowed!'.format(
              expr, base )

      return s.rtlir_tr_bit_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )
      
    elif isinstance( expr, PartSelection ):

      base = expr.get_base()
      if isinstance( base, (PartSelection, BitSelection) ):
        assert False,\
          'part selection {} over bit/part selection {} is not allowed!'.format(
              expr, base )

      start, stop = expr.get_slice()[0], expr.get_slice()[1]
      return s.rtlir_tr_part_selection(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        start, stop )

    elif isinstance( expr, ConstInstance ):

      dtype = expr.get_rtype().get_dtype()
      assert isinstance( dtype, Vector ),\
          '{} is not supported at L1!'.format( dtype )
      return s.rtlir_tr_literal_number( dtype.get_length(), expr.get_value() )

    # Other operations are not supported at L1

    else: assert False, '{} is not supported at L1!'.format( expr )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types

  def rtlir_tr_vector_dtype( s, Type ):
    raise NotImplementedError()

  def rtlir_tr_unpacked_array_type( s, Type ):
    raise NotImplementedError()

  # Declarations

  def rtlir_tr_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_port_decl( s, id_, Type, array_type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_wire_decls( s, wire_decls ):
    raise NotImplementedError()

  def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
    raise NotImplementedError()

  def rtlir_tr_const_decls( s, const_decls ):
    raise NotImplementedError()

  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):
    raise NotImplementedError()

  # Connections

  def rtlir_tr_connections( s, connections ):
    raise NotImplementedError()

  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_bit_selection( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_part_selection( s, base_signal, start, stop ):
    raise NotImplementedError()

  def rtlir_tr_port_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_wire_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_const_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_current_comp_attr( s, base_signal, attr ):
    raise NotImplementedError()

  def rtlir_tr_current_comp( s, comp_id, comp_rtype ):
    raise NotImplementedError()

  # Miscs

  def rtlir_tr_var_id( s, var_id ):
    raise NotImplementedError()

  def rtlir_tr_literal_number( s, nbits, value ):
    raise NotImplementedError()

  def rtlir_tr_component_unique_name( s, c_rtype ):
    raise NotImplementedError()
