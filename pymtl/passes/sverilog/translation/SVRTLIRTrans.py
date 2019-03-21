#=========================================================================
# SVRTLIRTrans.py
#=========================================================================
# Trans that implements the callback functions for translating PyMTL
# RTLIR into SystemVerilog.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl.passes.rtlir.translation import RTLIRTrans

from behavioral import SVBehavioralTrans
from structural import SVStructuralTrans

def mk_SVRTLIRTrans(
    _RTLIRTrans,
    _SVStructuralTrans = SVStructuralTrans,
    _SVBehavioralTrans = SVBehavioralTrans
  ):

  class _SVRTLIRTrans(
      _RTLIRTrans, _SVStructuralTrans, _SVBehavioralTrans
    ):

    @staticmethod
    def rtlir_tr_src_layout( value_types, component_src ):
      ret = ""
      ret = component_src
      return ret

    @staticmethod
    def rtlir_tr_components( components ):
      ret = ""
      for component in components:
        ret += component + '\n\n'
      return ret

    @staticmethod
    def rtlir_tr_component( component_nspace ):
      template =\
"""
module {module_name}
(
{port_decls}
);

{upblk_srcs}

endmodule
"""
      module_name = component_nspace.component_name
      port_decls  = component_nspace.port_decls
      upblk_srcs  = component_nspace.upblk_srcs

      return template.format( **locals() )

    @staticmethod
    def rtlir_tr_component_name( component_name ):
      return component_name

    @staticmethod
    def rtlir_tr_signal_name( signal_name ):
      return signal_name

  return _SVRTLIRTrans

SVRTLIRTrans = mk_SVRTLIRTrans(
    RTLIRTrans, SVStructuralTrans, SVBehavioralTrans
  )
