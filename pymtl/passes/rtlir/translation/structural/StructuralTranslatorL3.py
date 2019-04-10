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

    # Declarations

    s.structural.decl_ifcs = {}

    # Translate the definition of interfaces

    def_ifcs = []

    for ifc in top._pass_structural_rtlir_gen.ifcs:

      # Translate the interface wires ( not a specific view )

      interface_wires = []

      for wire_id, rtype in ifc.get_all_wires_packed():

        if isinstance( rtype, Array ):
          array_rtype = rtype
          wire_rtype = rtype.get_sub_type()
        else:
          array_rtype = None
          wire_rtype = rtype

        interface_wires.append(
          s.rtlir_tr_interface_wire_decl(
            s.rtlir_tr_var_id( wire_id ),
            wire_rtype,
            s.rtlir_tr_unpacked_array_type( array_rtype ),
            s.rtlir_data_type_translation( top, wire_rtype.get_dtype() )
        ) )

      ifc_wires = s.rtlir_tr_interface_wire_decls( interface_wires )

      # Translate the interface views

      interface_views = []

      for view in ifc.get_all_views():

        port_decls = []

        # Translate the direction of each port

        for port_id, rtype in view.get_all_ports_packed():

          if isinstance( rtype, Array ):
            array_rtype = rtype
            port_rtype = rtype.get_sub_type()
          else:
            array_rtype = None
            port_rtype = rtype

          port_decls.append(
            s.rtlir_tr_interface_view_port_direction(
              s.rtlir_tr_var_id( port_id ),
              port_rtype,
              s.rtlir_tr_unpacked_array_type( array_rtype )
            ) )

        interface_views.append( s.rtlir_tr_interface_view_decl(
          view, s.rtlir_tr_interface_view_port_directions( port_decls ) ) )

      # Append tuple ( InterfaceRType, InterfaceDef ) to the result array

      def_ifcs.append( ( ifc, s.rtlir_tr_interface_def(
        ifc, ifc_wires, s.rtlir_tr_interface_view_decls( interface_views )
      ) ) )

    s.structural.def_ifcs = def_ifcs
    super( StructuralTranslatorL3, s ).translate_structural( top )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Interfaces

    ifc_decls, ifc_defs = [], []

    for ifc_id, rtype in m_rtype.get_ifc_views_packed():

      if isinstance( rtype, Array ):
        array_rtype = rtype
        ifc_rtype = rtype.get_sub_type()
      else:
        array_rtype = None
        ifc_rtype = rtype

      ifc_decls.append(
        s.rtlir_tr_interface_port_decl(
          ifc_id,
          ifc_rtype,
          s.rtlir_tr_unpacked_array_type( array_rtype )
      ) )

    s.structural.decl_ifcs[m] = s.rtlir_tr_interface_port_decls( ifc_decls )

    # Verilator limitation: the top component cannot have interface ports

    # if m is s.top and ifc_decls:
      
      # assert False, 'top component {} cannot have interface port {}!'.format(
        # m, ifc_decls
      # )

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

      return s.rtlir_tr_interface_port_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    else:

      return super( StructuralTranslatorL3, s ).\
          rtlir_signal_expr_translation( expr, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Declarations

  def rtlir_tr_interface_port_decls( s, ifcs ):
    raise NotImplementedError()

  def rtlir_tr_interface_port_decl( s, ifc_id, ifc_rtype, array_type ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_port_directions( s, directions ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_port_direction( s, id_, rtype, array_type ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_decls( s, view_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_decl( s, view_rtype, directions ):
    raise NotImplementedError()

  def rtlir_tr_interface_wire_decls( s, wire_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_wire_decl( s, id_, rtype, array_type, dtype ):
    raise NotImplementedError()

  # Definitions

  def rtlir_tr_interface_defs( s, ifc_defs ):
    raise NotImplementedError()

  def rtlir_tr_interface_def( s, ifc_rtype, wire_defs, view_defs ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_interface_port_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    raise NotImplementedError()
