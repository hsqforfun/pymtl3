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

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata
from StructuralTranslatorL2 import StructuralTranslatorL2

class StructuralTranslatorL3( StructuralTranslatorL2 ):

  def __init__( s, top ):

    super( StructuralTranslatorL3, s ).__init__( top )

    # Declarations

    s.structural.decl_ifcs = {}

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

    # Translate the definition of interfaces

    def_ifcs = []

    for ifc in top._pass_structural_rtlir_gen.ifcs:

      # Translate the interface wires ( not a specific view )

      interface_wires = []

      for wire_name, wire_rtype in ifc.get_all_properties().iteritems():

        interface_wires.append(
          s.rtlir_tr_interface_wire_decl(
            s.rtlir_tr_var_name( wire_name ),
            wire_rtype,
            s.rtlir_data_type_translation( top, wire_rtype.get_dtype() )
        ) )

      ifc_wires = s.rtlir_tr_interface_wire_decls( interface_wires )

      # Translate the interface views

      interface_views = []

      for view in ifc.get_all_views():

        port_decls = []

        # Translate the direction of each port

        for port_name, port_rtype in view.get_all_properties().iteritems():

          port_decls.append(
            s.rtlir_tr_interface_view_port_direction(
              s.rtlir_tr_var_name( port_name ), port_rtype ) )

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

    for ifc_name, rtype in m_rtype.get_ifc_views():

      ifc_decls.append(
        s.rtlir_tr_interface_port_decl( ifc_name, rtype )
      )

    s.structural.decl_ifcs[m] = s.rtlir_tr_interface_port_decls( ifc_decls )

    # Verilator limitation: the top component cannot have interface ports

    # if m is s.top and ifc_decls:
      
      # assert False, 'top component {} cannot have interface port {}!'.format(
        # m, ifc_decls
      # )

    super( StructuralTranslatorL3, s ).translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_signal_translation
  #-----------------------------------------------------------------------
  # Translate a PyMTL dsl signal object into its backend representation.

  # Override
  def rtlir_signal_translation( s, obj, m ):

    def is_ifc_attribute( signal ):

      if isinstance( signal._dsl.parent_obj, pymtl.dsl.Interface ) and\
         signal in signal._dsl.parent_obj.__dict__.values():

        return True

      else: return False

    # L3: obj must be a signal/ifc that belongs to the current component. No
    # subcomponent is allowed at this level.
    # `obj` here should be a PyMTL Connectable instance

    # Signal ( Port, Wire ) connectable

    if isinstance( obj, pymtl.dsl.Signal ):

      # `obj` is an attribute of an interface

      if is_ifc_attribute( obj ):

        return s.rtlir_tr_interface_attr(
          s.rtlir_signal_translation( obj._dsl.parent_obj, m ),
          obj._dsl.my_name
        )

      else:

        return super( StructuralTranslatorL3, s ).\
            rtlir_signal_translation( obj, m )

    # Const connetable

    elif isinstance( obj, pymtl.dsl.Const ):

      # Constant objects cannot be the attribute of an interface

      if is_ifc_attribute( obj ):

        assert False, '{} is not a port object of interface {}!'.format(
            obj, obj._dsl.parent_obj )

      else:

        return super( StructuralTranslatorL3, s ).\
            rtlir_signal_translation( obj, m )

    # Interface connectable

    elif isinstance( obj, pymtl.dsl.Interface ):

      # Interface `obj` is an attribute of another interface

      if is_ifc_attribute( obj ):

        return s.rtlir_tr_interface_attr(
          s.rtlir_tr_interface_attr( obj._dsl.parent_obj, m ),
          obj._dsl.my_name
        )

      # Refer to the interface object of the current component

      elif ( 'level' in obj._dsl.__dict__ ):

        m_level = m._dsl.level
        obj_level = obj._dsl.level

        assert obj_level == ( m_level + 1 ),\
"{} is not an attribute of component {}. Subcomponent is not supported at L3!"\
          .format( obj, m )

        return s.rtlir_tr_var_name( obj._dsl.my_name )

      # Unrecognized signal expression...

      else:

        assert False, 'unknown signal expression {} at L3!'.format( obj )

    # Everything else belongs to the previous levels

    else:

      return super( StructuralTranslatorL3, s ).\
          rtlir_signal_translation( obj, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Declarations

  def rtlir_tr_interface_port_decls( s, ifcs ):
    raise NotImplementedError()

  def rtlir_tr_interface_port_decl( s, ifc_name, ifc_decl ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_port_directions( s, directions ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_port_direction( s, name, rtype ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_decls( s, view_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_view_decl( s, view_rtype ):
    raise NotImplementedError()

  def rtlir_tr_interface_wire_decls( s, wire_decls ):
    raise NotImplementedError()

  def rtlir_tr_interface_wire_decl( s, name, rtype ):
    raise NotImplementedError()

  # Definitions

  def rtlir_tr_interface_defs( s, ifc_defs ):
    raise NotImplementedError()

  def rtlir_tr_interface_def( s, ifc_rtype, wire_defs, view_defs ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    raise NotImplementedError()
