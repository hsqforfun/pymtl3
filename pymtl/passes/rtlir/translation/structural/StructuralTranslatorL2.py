#=========================================================================
# StructuralTranslatorL2.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 24, 2019

import inspect, pymtl

from collections import defaultdict, deque

from pymtl.passes.utility import *
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL2Pass\
    import StructuralRTLIRGenL2Pass

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata
from StructuralTranslatorL1 import StructuralTranslatorL1

class StructuralTranslatorL2( StructuralTranslatorL1 ):

  def __init__( s, top ):

    super( StructuralTranslatorL2, s ).__init__( top )

    # Declarations

    s.structural.decl_type_struct = []

  #-----------------------------------------------------------------------
  # gen_structural_trans_metadata
  #-----------------------------------------------------------------------

  # Override
  def gen_structural_trans_metadata( s, top ):

    top.apply( StructuralRTLIRGenL2Pass() )

  #-----------------------------------------------------------------------
  # _translate_structural
  #-----------------------------------------------------------------------

  # Override
  def _translate_structural( s, m ):

    super( StructuralTranslatorL2, s )._translate_structural( m )

  #-----------------------------------------------------------------------
  # translate_decls
  #-----------------------------------------------------------------------

  # Override
  def translate_decls( s, m ):

    super( StructuralTranslatorL2, s ).translate_decls( m )

  #-----------------------------------------------------------------------
  # rtlir_data_type_translation
  #-----------------------------------------------------------------------
  # Translate an RTLIR data type into its backend representation.

  # Override
  def rtlir_data_type_translation( s, m, dtype ):

    if isinstance( dtype, Struct ):

      ret = s.rtlir_tr_struct_dtype( dtype )

      if reduce( lambda r, x: r and dtype != x[0],
          s.structural.decl_type_struct, True ):

        s.structural.decl_type_struct.append( ( dtype, ret ) )

      return ret

    else:

      return super( StructuralTranslatorL2, s ).\
          rtlir_data_type_translation( m, dtype )

  #-----------------------------------------------------------------------
  # rtlir_signal_translation
  #-----------------------------------------------------------------------
  # Translate a PyMTL dsl signal object into its backend representation.

  # Override
  def rtlir_signal_translation( s, obj, m ):

    def is_struct_attribute( signal ):

      if isinstance( signal._dsl.parent_obj, pymtl.dsl.Signal ) and\
         hasattr( signal._dsl.parent_obj._dsl, 'attrs' ) and\
         signal._dsl.my_name in signal._dsl.parent_obj._dsl.attrs:

        ptype = signal._dsl.parent_obj._dsl.Type

        return not is_BitsX( ptype ) and\
               not type( ptype ).__name__ in dir( __builtins__ )

      else: return False

    # L2: obj must be a signal that belongs to the current component. No
    # subcomponent is allowed at this level.
    # `obj` here should be a PyMTL Connectable instance

    # Signal ( Port, Wire ) connectable

    if isinstance( obj, pymtl.dsl.Signal ):

      # struct attribute access

      if is_struct_attribute( obj ):

        return s.rtlir_tr_struct_attr(
          s.rtlir_signal_translation( obj._dsl.parent_obj, m ),
          obj._dsl.my_name
        )

      else:

        return super( StructuralTranslatorL2, s ).\
            rtlir_signal_translation( obj, m )

    # Const connectable

    elif isinstance( obj, pymtl.dsl.Const ):

      assert is_BitsX( obj._dsl.Type ),\
        'translating struct const {} is not supported!'.format( obj )

      return super( StructuralTranslatorL2, s ).\
          rtlir_signal_translation( obj, m )

    else:
      
      return super( StructuralTranslatorL2, s ).\
          rtlir_signal_translation( obj, m )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  # Data types

  def rtlir_tr_struct_dtype( s, Type ):
    raise NotImplementedError()

  # Signal operations
  
  def rtlir_tr_struct_attr( s, base_signal, attr ):
    raise NotImplementedError()
