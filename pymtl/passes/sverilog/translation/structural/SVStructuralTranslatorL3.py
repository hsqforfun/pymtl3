#=========================================================================
# SVStructuralTranslatorL3.py
#=========================================================================
# The methods that are commented out were used to generate SystemVerilog
# interface definitions.

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL3\
    import StructuralTranslatorL3
from pymtl.passes.rtlir.RTLIRType import *

from SVStructuralTranslatorL2 import SVStructuralTranslatorL2

class SVStructuralTranslatorL3(
    SVStructuralTranslatorL2, StructuralTranslatorL3
  ):

  # Declarations

  def rtlir_tr_interface_port_decls( s, port_decls ):
    return port_decls

  def rtlir_tr_interface_port_decl( s, port_id, port_rtype, port_array_type,
      port_dtype ):
    decl_tmplt = port_rtype.get_direction() + ' ' +\
                 port_dtype['decl'] + '_' + port_id + ' ' +\
                 port_array_type['decl']
    return decl_tmplt

  def rtlir_tr_interface_decls( s, ifc_decls ):
    all_decls = reduce( lambda res, l: res + l, ifc_decls, [] )
    make_indent( all_decls, 1 )
    return ',\n'.join( all_decls )

  def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type,
      port_decls ):
    def gen_interface_array_decl( ifc_id, ifc_rtype, n_dim, c_n_dim,
        port_decls ):
      ret = []
      if not n_dim:
        id_ = ifc_id + c_n_dim
        return map( lambda pdecl: pdecl.format(id_ = id_), port_decls )

      else:
        return reduce( lambda res, l: res+l, map(
          lambda idx: gen_interface_array_decl(
            ifc_id, ifc_rtype, n_dim[1:0], c_n_dim+'_$'+str(idx), port_decls
        ), xrange( n_dim[0] ) ), [] )

    n_dim = array_type['n_dim']
    return\
      gen_interface_array_decl( ifc_id, ifc_rtype, n_dim, '', port_decls )

  # Signal operations

  def rtlir_tr_interface_array_index( s, base_signal, index ):
    return '{base_signal}_${index}'.format( **locals() )

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    return '{base_signal}_{attr}'.format( **locals() )
