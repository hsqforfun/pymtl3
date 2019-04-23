#=========================================================================
# StructuralTranslatorL3.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : Apr 4, 2019

import inspect, pymtl

from collections import defaultdict, deque

from pymtl.passes.utility import *
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL3Pass\
    import StructuralRTLIRGenL3Pass
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr\
    import *

from StructuralTranslatorL2 import StructuralTranslatorL2

class StructuralTranslatorL3( StructuralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, top ):

    top.apply( StructuralRTLIRGenL3Pass() )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, top ):

    s.structural.decl_ifcs = {}

    # Generate definitions for interfaces

    # ifc_defs = []
    # ifcs = top._pass_structural_rtlir_gen.ifcs
    # for ifc_name, ifc_rtype in ifcs:

      # ifc_ports = []
      # for port_id, rtype in ifc_rtype.get_all_ports_packed():
        # if isinstance( rtype, Array ):
          # port_array_rtype = rtype
          # port_rtype = rtype.get_sub_type()
        # else:
          # port_array_rtype = None
          # port_rtype = rtype

        # ifc_ports.append(
          # s.rtlir_tr_interface_def_port_decl(
            # s.rtlir_tr_var_id( port_id ),
            # port_rtype,
            # s.rtlir_tr_unpacked_array_type( port_array_type ),
            # s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
        # ) )

      # ifc_defs.append( s.rtlir_tr_interface_def(
        # ifc_name, ifc_rtype,
        # s.rtlir_tr_interface_def_port_decls( ifc_ports )
      # ) )
    # s.structural.def_ifcs = s.rtlir_tr_interface_defs( ifc_defs )

    super( StructuralTranslatorL3, s ).translate_structural( top )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Interfaces

    ifc_decls = []

    for ifc_id, rtype in m_rtype.get_ifc_views_packed():

      if isinstance( rtype, Array ):
        array_rtype = rtype
        ifc_rtype = rtype.get_sub_type()
      else:
        array_rtype = None
        ifc_rtype = rtype

      ports = []
      for port_id, p_rtype in ifc_rtype.get_all_ports_packed():
        if isinstance( p_rtype, Array ):
          port_array_rtype = p_rtype
          port_rtype = p_rtype.get_sub_type()
        else:
          port_array_rtype = None
          port_rtype = p_rtype

        ports.append( s.rtlir_tr_interface_port_decl(
          s.rtlir_tr_var_id( port_id ),
          port_rtype,
          s.rtlir_tr_unpacked_array_type( port_array_rtype ),
          s.rtlir_data_type_translation( m, port_rtype.get_dtype() )
        ) )

      ifc_decls.append(
        s.rtlir_tr_interface_decl(
          ifc_id,
          ifc_rtype,
          s.rtlir_tr_unpacked_array_type( array_rtype ),
          s.rtlir_tr_interface_port_decls( ports )
      ) )

      # ifc_decls.append(
        # s.rtlir_tr_interface_decl(
          # ifc_id,
          # ifc_rtype,
          # s.rtlir_tr_unpacked_array_type( array_rtype )
      # ) )

    s.structural.decl_ifcs[m] = s.rtlir_tr_interface_decls( ifc_decls )

    super( StructuralTranslatorL3, s ).translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------
  # Translate a signal expression in RTLIR into its backend representation.
  # Add support for the following operations at L3:
  # InterfaceAttr

  # Override
  def rtlir_signal_expr_translation( s, expr, m ):

    if isinstance( expr, InterfaceAttr ):

      return s.rtlir_tr_interface_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr() )

    elif isinstance( expr, InterfaceViewIndex ):

      return s.rtlir_tr_interface_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    else:

      return super( StructuralTranslatorL3, s ).\
          rtlir_signal_expr_translation( expr, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------
  # The methods that are commented out were used to generate SystemVerilog
  # interface definitions.

  # Definitions

  def rtlir_tr_interface_def( s, ifc_name, ifc_rtype, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_defs( s, ifc_defs ):
    raise NotImplementedError()

  def rtlir_tr_interface_def_port_decl( s, port_id, port_rtype,
      port_array_type, port_data_type ):
    raise NotImplementedError()

  def rtlir_tr_interface_def_port_decls( s, port_decls ):
    raise NotImplementedError()

  # Declarations

  def rtlir_tr_interface_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_port_decl( s, port_id, port_rtype, port_array_type,
      port_dtype ):
    raise NotImplementedError()

  def rtlir_tr_interface_decls( s, ifc_decls ):
    raise NotImplementedError()

  # def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type ):
      # port_decls ):
  def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type,
      port_decls ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_interface_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    raise NotImplementedError()
