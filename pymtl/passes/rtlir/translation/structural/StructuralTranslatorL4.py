#=========================================================================
# StructuralTranslatorL4.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : Apr 4, 2019

import inspect, pymtl

from collections import defaultdict, deque

from pymtl.passes.utility import *
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL4Pass\
    import StructuralRTLIRGenL4Pass
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr\
    import *

from StructuralTranslatorL3 import StructuralTranslatorL3

class StructuralTranslatorL4( StructuralTranslatorL3 ):

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, top ):

    top.apply( StructuralRTLIRGenL4Pass() )

  #-----------------------------------------------------------------------
  # translate_structural
  #-----------------------------------------------------------------------

  # Override
  def translate_structural( s, top ):

    s.structural.decl_subcomps = {}
    super( StructuralTranslatorL4, s ).translate_structural( top )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  # Override
  def _translate_structural( s, m ):

    super( StructuralTranslatorL4, s )._translate_structural( m )

    for child in m.get_child_components():

      s._translate_structural( child )

  # Override
  def translate_decls( s, m ):

    super( StructuralTranslatorL4, s ).translate_decls( m )

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Translate subcomponent declarations

    subcomp_decls = []

    for c_id, _c_rtype in m_rtype.get_subcomps_packed():

      if isinstance( _c_rtype, Array ):
        c_array_rtype = _c_rtype
        c_rtype = _c_rtype.get_sub_type()
      else:
        c_array_rtype = None
        c_rtype = _c_rtype

      # For a subcomponent translate the connections of its value ports and
      # interface ports

      port_conns, ifc_conns = [], []

      for port_id, _port_rtype in c_rtype.get_ports_packed():

        if isinstance( _port_rtype, Array ):
          port_array_rtype = _port_rtype
          port_rtype = _port_rtype.get_sub_type()
        else:
          port_array_rtype = None
          port_rtype = _port_rtype

        port_conns.append( s.rtlir_tr_subcomp_port_decl(
          c_id, c_rtype, port_id, port_rtype,
          s.rtlir_tr_unpacked_array_type( port_array_rtype )
        ) )

      for ifc_port_id, _ifc_port_rtype in c_rtype.get_ifc_views_packed():

        if isinstance( _ifc_port_rtype, Array ):
          ifc_port_array_rtype = _ifc_port_rtype
          ifc_port_rtype = _ifc_port_rtype.get_sub_type()
        else:
          ifc_port_array_rtype = None
          ifc_port_rtype = _ifc_port_rtype

        ports = []
        for port_id, p_rtype in ifc_port_rtype.get_all_ports_packed():
          if isinstance( p_rtype, Array ):
            port_array_rtype = p_rtype
            port_rtype = p_rtype.get_sub_type()
          else:
            port_array_rtype = None
            port_rtype = p_rtype

          ports.append( s.rtlir_tr_subcomp_port_decl(
            '{c_id}', c_rtype,
            ifc_port_id + '{ifc_n_dim}_' + port_id,
            port_rtype,
            s.rtlir_tr_unpacked_array_type( port_array_rtype )
          ) )

        # s.structural.decl_ifcs[m] = s.rtlir_tr_interface_decls( ifc_decls )

        ifc_conns.append( s.rtlir_tr_subcomp_ifc_port_decl(
          '{c_id}', c_rtype, ifc_port_id, ifc_port_rtype,
          s.rtlir_tr_unpacked_array_type( ifc_port_array_rtype ),
          s.rtlir_tr_subcomp_port_decls( ports )
        ) )

      # Generate a list of port/interface connections

      subcomp_decls.append( s.rtlir_tr_subcomp_decl(
        c_id, c_rtype,
        s.rtlir_tr_subcomp_port_decls( port_conns ),
        s.rtlir_tr_subcomp_ifc_port_decls( ifc_conns ),
        s.rtlir_tr_unpacked_array_type( c_array_rtype )
      ) )

    s.structural.decl_subcomps[m] = s.rtlir_tr_subcomp_decls( subcomp_decls )

  #-----------------------------------------------------------------------
  # rtlir_signal_expr_translation
  #-----------------------------------------------------------------------
  # Translate a signal expression in RTLIR into its backend representation.
  # Add support for the following operations at L4:
  # SubCompAttr

  def rtlir_signal_expr_translation( s, expr, m ):

    if isinstance( expr, SubCompAttr ):

      return s.rtlir_tr_subcomp_attr(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_attr() )

    elif isinstance( expr, ComponentIndex ):

      return s.rtlir_tr_component_array_index(
        s.rtlir_signal_expr_translation( expr.get_base(), m ),
        expr.get_index() )

    else: return super( StructuralTranslatorL4, s ).\
              rtlir_signal_expr_translation( expr, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend
  #-----------------------------------------------------------------------

  # Declarations

  def rtlir_tr_subcomp_port_decls( s, port_decls ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_port_decl( s, c_id, c_rtype, port_id, port_rtype,
      array_type, c_array_type ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_port_decls( s, ifc_port_decls ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_ifc_port_decl( s, c_id, c_rtype, ifc_port_id,
      ifc_port_rtype, ifc_port_array_type, c_array_type ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_decls( s, subcomps ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_decl( s, c_id, c_rtype, port_conns, ifc_conns,
      array_type, c_array_type ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_component_array_index( s, base_signal, index ):
    raise NotImplementedError()

  def rtlir_tr_subcomp_attr( s, base_signal, attr ):
    raise NotImplementedError()
