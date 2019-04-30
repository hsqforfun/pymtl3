#=========================================================================
# SVRTLIRTranslator.py
#=========================================================================
# Trans that implements the callback functions for translating PyMTL
# RTLIR into SystemVerilog.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl.passes.sverilog.utility import get_string
from pymtl.passes.rtlir.translation import RTLIRTranslator

from pymtl.passes.rtlir.behavioral import MinBehavioralRTLIRLevel,\
                                          MaxBehavioralRTLIRLevel
from pymtl.passes.rtlir.structural import MinStructuralRTLIRLevel,\
                                          MaxStructuralRTLIRLevel

def mk_SVRTLIRTranslator( _RTLIRTranslator, b_level, s_level ):

  assert MinBehavioralRTLIRLevel <= b_level <= MaxBehavioralRTLIRLevel
  assert MinStructuralRTLIRLevel <= s_level <= MaxStructuralRTLIRLevel

  behavioral_tplt =\
    'from behavioral import SVBehavioralTranslatorL{} as SVBehavioralTranslator'

  structural_tplt =\
    'from structural import SVStructuralTranslatorL{} as SVStructuralTranslator'

  exec behavioral_tplt.format( b_level ) in globals(), locals()
  exec structural_tplt.format( s_level ) in globals(), locals()

  class _SVRTLIRTranslator(
      _RTLIRTranslator, SVBehavioralTranslator, SVStructuralTranslator
    ):

    def rtlir_tr_src_layout( s, hierarchy ):

      ret = ""

      # Add struct definitions

      for struct_dtype, tplt in hierarchy.decl_type_struct:

        ret += tplt['def'] + '\n'

      # Add interface definitions

      for ifc_type, ifc_def in hierarchy.def_ifcs:

        ret += ifc_def + '\n'

      # Add component sources

      ret += hierarchy.component_src
      return ret

    def rtlir_tr_components( s, components ):

      ret = ""

      for component in components:

        ret += component + '\n\n'

      return ret

    def rtlir_tr_component( s, behavioral, structural ):

      template =\
"""
module {module_name}
(
{port_decls}
{ifc_decls}
);
{const_decls}
{behavioral_fvars}

{wire_decls}

{subcomp_decls}

{upblk_srcs}

{connections}

endmodule
"""
      module_name = getattr( structural, 'component_unique_name', '' )

      port_decls = getattr( structural, 'decl_ports', '' )
      ifc_decls = getattr( structural, 'decl_ifcs', '' )
      if port_decls and ifc_decls: port_decls += ','

      wire_decls = getattr( structural, 'decl_wires', '' )
      const_decls = getattr( structural, 'decl_consts', '' )
      subcomp_decls = getattr( structural, 'decl_subcomps', '' )
      upblk_srcs = getattr( behavioral, 'upblk_srcs', '' )
      behavioral_fvars = getattr( behavioral, 'decl_freevars', '' )
      connections = getattr( structural, 'connections', '' )

      s._top_module_name = module_name

      return template.format( **locals() )

  return _SVRTLIRTranslator

SVRTLIRTranslator = mk_SVRTLIRTranslator( RTLIRTranslator,
    MaxBehavioralRTLIRLevel, MaxStructuralRTLIRLevel )
