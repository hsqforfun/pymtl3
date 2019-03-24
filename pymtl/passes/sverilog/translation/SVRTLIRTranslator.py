#=========================================================================
# SVRTLIRTranslator.py
#=========================================================================
# Trans that implements the callback functions for translating PyMTL
# RTLIR into SystemVerilog.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl.passes.rtlir.translation import RTLIRTranslator

from behavioral import SVBehavioralTranslator
from structural import SVStructuralTranslator

def mk_SVRTLIRTranslator(
    _RTLIRTranslator,
    _SVBehavioralTranslator = SVBehavioralTranslator,
    _SVStructuralTranslator = SVStructuralTranslator
  ):

  class _SVRTLIRTranslator(
      _RTLIRTranslator, _SVBehavioralTranslator, _SVStructuralTranslator
    ):

    @staticmethod
    def rtlir_tr_src_layout( hierarchy_nspace ):
      ret = ""
      ret = hierarchy_nspace.components
      return ret

    @staticmethod
    def rtlir_tr_components( components ):
      ret = ""
      for component in components:
        ret += component + '\n\n'
      return ret

  return _SVRTLIRTranslator

SVRTLIRTranslator = mk_SVRTLIRTranslator(
    RTLIRTranslator, SVBehavioralTranslator, SVStructuralTranslator
  )
