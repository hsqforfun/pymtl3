#=========================================================================
# SVRTLIRTranslator.py
#=========================================================================
# Trans that implements the callback functions for translating PyMTL
# RTLIR into SystemVerilog.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl.passes.rtlir.translation import RTLIRTranslator

def mk_SVRTLIRTranslator( _RTLIRTranslator, b_level=1, s_level=1 ):

  assert 0 <= b_level <= 2 and 1 <= s_level <= 1

  if b_level == 0:
    from behavioral import SVBehavioralTranslatorL0 as SVBehavioralTranslator
  elif b_level == 1:
    from behavioral import SVBehavioralTranslatorL1 as SVBehavioralTranslator
  elif b_level == 2:
    from behavioral import SVBehavioralTranslatorL2 as SVBehavioralTranslator
  else: assert False

  if s_level == 1:
    from structural import SVStructuralTranslatorL1 as SVStructuralTranslator
  else: assert False

  class _SVRTLIRTranslator(
      _RTLIRTranslator, SVBehavioralTranslator, SVStructuralTranslator
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

SVRTLIRTranslator = mk_SVRTLIRTranslator( RTLIRTranslator )
