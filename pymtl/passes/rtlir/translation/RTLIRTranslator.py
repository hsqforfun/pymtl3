#=========================================================================
# RTLIRTranslator.py
#=========================================================================
# A framework for translating a PyMTL RTLComponent into arbitrary backend
# by calling user-defined translation callbacks.
#
# Author : Peitian Pan
# Date   : March 15, 2019

import inspect

from pymtl.passes.utility import get_string

from behavioral import BehavioralTranslatorL1
from structural import StructuralTranslatorL1

def mk_RTLIRTranslator( _BehavioralTranslator, _StructuralTranslator ):
  """
     Construct an RTLIRTranslator from the two given translators. This
     allows incremental development and testing.
  """

  class _RTLIRTranslator( _BehavioralTranslator, _StructuralTranslator ):

    # Override
    def __init__( s, top ):

      super( _RTLIRTranslator, s ).__init__( top )

    # Override
    def translate( s ):

      s.translate_behavioral( s.top )
      s.translate_structural( s.top )

      s.hierarchy.components = s.__class__.rtlir_tr_components(
        s.hierarchy.component_srcs
      )

      s.hierarchy.src = s.__class__.rtlir_tr_src_layout( s.hierarchy )

    #---------------------------------------------------------------------
    # Methods to be implemented by the backend translator
    #---------------------------------------------------------------------

    @staticmethod
    def rtlir_tr_src_layout( hierarchy_nspace ):
      raise NotImplementedError()

    @staticmethod
    def rtlir_tr_components( components ):
      raise NotImplementedError()

  return _RTLIRTranslator

RTLIRTranslator = mk_RTLIRTranslator( BehavioralTranslatorL1, StructuralTranslatorL1 )
