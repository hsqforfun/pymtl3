#=========================================================================
# SVRTLIRTranslator.py
#=========================================================================
# Trans that implements the callback functions for translating PyMTL
# RTLIR into SystemVerilog.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl.passes.utility import get_string
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
# (
{const_decls}
)
(
{port_decls}
{ifc_decls}
);

{wire_decls}

{upblk_srcs}

{connections}

endmodule
"""

      comp_name = getattr( structural, 'component_name', '' )
      comp_param = getattr( structural, 'component_param', None )
      comp_argspec = getattr( structural, 'component_argspec', None )
      module_name = s.gen_module_name( comp_name, comp_param, comp_argspec )

      port_decls = getattr( structural, 'decl_ports', '' )
      ifc_decls = getattr( structural, 'decl_ifcs', '' )
      if port_decls and ifc_decls: port_decls += ','

      wire_decls = getattr( structural, 'decl_wires', '' )
      const_decls = getattr( structural, 'decl_consts', '' )
      connections = getattr( structural, 'connections', '' )
      upblk_srcs = getattr( behavioral, 'upblk_srcs', '' )

      s._top_module_name = module_name

      return template.format( **locals() )

    #-----------------------------------------------------------------------
    # gen_module_name
    #-----------------------------------------------------------------------

    def gen_module_name( s, comp_name, comp_param, comp_argspec ):

      assert comp_name and comp_param

      # Add const args to module name

      for idx, arg_name in enumerate( comp_argspec.args[1:] ):

        arg_value = comp_param[ '' ][idx]
        comp_name += '__' + arg_name + '_' + get_string(arg_value)

      # Add varargs to module name

      if len( comp_param[''] ) > len( comp_argspec.args[1:] ):

        comp_name += '__' + comp_argspec.varargs
      
      for arg_value in comp_param[''][ len(comp_argspec.args[1:]): ]:

        comp_name += '___' + get_string(arg_value)

      # Add kwargs to module name

      for arg_name, arg_value in comp_param.iteritems():

        if arg_name == '': continue
        comp_name += '__' + arg_name + '_' + get_string(arg_value)

      return comp_name

  return _SVRTLIRTranslator

SVRTLIRTranslator = mk_SVRTLIRTranslator( RTLIRTranslator,
    MaxBehavioralRTLIRLevel, MaxStructuralRTLIRLevel )
