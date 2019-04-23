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

  # Definitions

  def rtlir_tr_interface_defs( s, ifc_defs ):
    return '\n'.join( ifc_defs )

  def rtlir_tr_interface_def( s, ifc_name, ifc_rtype, port_decls ):
    if not hasattr( s.s_backend, 'ifc_helpers' ):
      s.s_backend.ifc_helpers = []
    flattened_ports = port_decls['helper_port']
    ifc_to_port_assignments = port_decls['helper_assignment']
    ifc_helper_tmplt = \
"""\
module _{ifc_name}_helper( {ifc_name}.HelperSide _ifc, {flattened_ports} );
{ifc_to_port_assignments}
endmodule
"""
    s.s_backend.ifc_helpers.append(
      ( ifc_name, ifc_helper_tmplt.format( **locals() ) ) )
    ifc_wire_decls = port_decls['decl']
    mod_side_directions = port_decls['mod_directions']
    helper_side_directions = port_decls['helper_directions']
    ifc_tmplt = \
"""\
interface {ifc_name};
{ifc_wire_decls}
modport ModuleSide(
{mod_side_directions}
);
modport HelperSide(
{helper_side_directions}
);
endinterface
"""
    return ifc_tmplt.format( **locals() )

  def rtlir_tr_interface_def_port_decls( s, port_decls ):
    decls = map( lambda x: x['decl'], port_decls )
    mod_directions = map( lambda x: x['mod_direction'], port_decls )
    helper_directions = map( lambda x: x['helper_direction'], port_decls )
    helper_ports = map( lambda x: x['helper_port'], port_decls )
    helper_assignments = map( lambda x: x['helper_assignment'], port_decls )
    make_indent( decls, 1 )
    make_indent( mod_directions, 1 )
    make_indent( helper_directions, 1 )
    make_indent( helper_assignments, 1 )
    return {
      'decl': '\n'.join( decls ),
      'mod_direction': ',\n'.join( mod_directions ),
      'helper_direction': ',\n'.join( helper_directions ),
      'helper_port': ', '.join( helper_ports ),
      'helper_assignment': '\n'.join( helper_assignments )
    }

  def rtlir_tr_interface_def_port_decl( s, port_id, port_rtype,
      port_array_type, port_data_type ):
    wire_rtype = Wire( port_rtype.get_dtype(), port_rtype.unpacked )
    mod_direction = port_rtype.get_direction()
    helper_direction = 'input' if mod_direction=='output' else 'output'
    h_port_rtype = Port( helper_direction, port_rytpe.get_dtype(),
        port_rtype.unpacked )
    if helper_direction == 'input':
      lhs = '_ifc.{port_id}'.format( **locals() )
      rhs = '{port_id}'.format( **locals() )
    else:
      lhs = '{port_id}'.format( **locals() )
      rhs = '_ifc.{port_id}'.format( **locals() )
    return {
      'decl': s.rtlir_tr_wire_decl( port_id, wire_rtype, port_array_type,
        port_data_type ),
      'mod_direction': mod_direction + " " + port_id,
      'helper_direction': helper_direction + " " + port_id,
      'helper_port': s.rtlir_tr_port_decl( port_id, h_port_rtype,
        port_array_type, port_data_type ),
      'helper_assignment': 'assign {lhs} = {rhs};'.format( **locals() )
    }

  # Declarations

  # def rtlir_tr_interface_decls( s, ifc_decls ):
    # return ',\n'.join( ifc_decls )

  # def rtlir_tr_interface_decl( s, ifc_id, ifc_rtype, array_type ):
    # ifc_name = ifc_rtype.get_name()
    # array_dim = array_type['decl']
    # return '{ifc_name}.ModuleSide {ifc_id} {array_dim}'.format( **locals() )

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
    # return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    return '{base_signal}_{attr}'.format( **locals() )
    # return '{base_signal}.{attr}'.format( **locals() )
