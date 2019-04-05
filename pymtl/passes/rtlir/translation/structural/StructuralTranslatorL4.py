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

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata
from StructuralTranslatorL3 import StructuralTranslatorL3

class StructuralTranslatorL4( StructuralTranslatorL3 ):

  def __init__( s, top ):

    super( StructuralTranslatorL4, s ).__init__( top )

    # Declarations

    s.structural.decl_ifcs = {}
    s.structural.def_ifcs = {}

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, top ):

    top.apply( StructuralRTLIRGenL4Pass() )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):

    m_rtype = m._pass_structural_rtlir_gen.rtlir_type

    # Interfaces

    ifc_decls, ifc_defs = [], []

    for ifc_name, rtype in m_rtype.get_ifcs():

      ifc_decl = []

      ifc_decls.append(
        s.rtlir_tr_interface_decl( ifc_name, rtype )
      )

      # Generate declaration for each field of the interface

      for sig_name, sig_rtype in rtype.get_all_properties().iteritems():

        if isinstance( sig_rtype, Port ):

          ifc_decl.append(
            s.rtlir_tr_interface_port_decl(
              s.rtlir_tr_var_name( ifc_name ),
              rtype,
              s.rtlir_tr_var_name( sig_name ),
              sig_rtype,
              s.rtlir_data_type_translation( m, sig_rtype.get_dtype() )
          ) )

        elif isinstance( sig_rtype, Wire ):

          ifc_decl.append(
            s.rtlir_tr_interface_wire_decl(
              s.rtlir_tr_var_name( ifc_name ),
              rtype,
              s.rtlir_tr_var_name( sig_name ),
              sig_rtype,
              s.rtlir_data_type_translation( m, sig_rtype.get_dtype() )
          ) )

        elif isinstance( sig_rtype, Interface ):

          ifc_decl.append(
            s.rtlir_tr_interface_interface_decl(
              s.rtlir_tr_var_name( ifc_name ),
              rtype,
              s.rtlir_tr_var_name( sig_name ),
              sig_rtype
          ) )
        
        else: assert False

      if not rtype.get_name() in map( lambda x: x[0].get_name(), ifc_defs ):

        ifc_defs.append( (
          rtype,
          s.rtlir_tr_interface_def( rtype.get_name(), ifc_decl ) ) )

    s.structural.decl_ifcs[m] = s.rtlir_tr_interface_decls( ifc_decls )
    s.structural.def_ifcs[m] = ifc_defs

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

  def rtlir_tr_interface_decls( s, ifcs ):
    raise NotImplementedError()

  def rtlir_tr_interface_decl( s, ifc_name, ifc_decl ):
    raise NotImplementedError()

  def rtlir_tr_interface_port_decl(
      s, ifc_name, ifc_rtype, port_name, port_rtype, port_dtype ):
    raise NotImplementedError()

  def rtlir_tr_interface_wire_decl(
      s, ifc_name, ifc_rtype, wire_name, wire_rtype, wire_dtype ):
    raise NotImplementedError()

  def rtlir_tr_interface_interface_decl(
      s, ifc_name, ifc_rtype, ifc_name2, ifc_rtype2 ):
    raise NotImplementedError()

  # Definitions

  def rtlir_tr_interface_def( s, ifc_type_name, ifc_decl ):
    raise NotImplementedError()

  # Signal operations

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    raise NotImplementedError()
