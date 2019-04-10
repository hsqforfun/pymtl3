#=========================================================================
# SVStructuralTranslatorL3.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL3\
    import StructuralTranslatorL3
from pymtl.passes.rtlir.RTLIRType import *

from SVStructuralTranslatorL2 import SVStructuralTranslatorL2

class SVStructuralTranslatorL3(
    SVStructuralTranslatorL2, StructuralTranslatorL3
  ):

  # Declarations

  def rtlir_tr_interface_port_decls( s, ifc_decls ):
    decls = reduce( lambda res, l: res+l, ifc_decls, [] )
    make_indent( decls, 1 )
    return ',\n'.join( decls )

  def rtlir_tr_interface_port_decl( s, ifc_view_id, ifc_view_rtype,
      array_type ):
    def gen_ifc_port_array( n_dim, ifc_name, ifc_view_name, ifc_view_id, tplt ):
      if not n_dim:
        return [ tplt.format( **locals() ) ]
      return reduce ( lambda res, l: res+l, map( lambda idx: gen_ifc_port_array(
        n_dim[1:], ifc_name, ifc_view_name, ifc_view_id+'_$'+str(idx), tplt ),
        xrange( n_dim[0] )
      ), [] )

    n_dims = array_type['n_dim']
    ifc_name = ifc_view_rtype.get_interface().get_name()
    ifc_view_name = ifc_view_rtype.get_name()
    tplt = '{ifc_name}.{ifc_view_name} {ifc_view_id}'
    return\
      gen_ifc_port_array( n_dims, ifc_name, ifc_view_name, ifc_view_id, tplt )
    # return '{ifc_name}.{ifc_view_name} {ifc_view_id}'.format(**locals())

  def rtlir_tr_interface_view_port_directions( s, directions ):
    make_indent( directions, 2 )
    return ',\n'.join( directions )

  def rtlir_tr_interface_view_port_direction( s, port_id, port_rtype,
      array_type ):
    return port_rtype.get_direction() + ' ' + port_id

  def rtlir_tr_interface_view_decls( s, view_decls ):
    return '\n'.join( view_decls )

  def rtlir_tr_interface_view_decl( s, view_rtype, port_direction ):

    view_name = view_rtype.get_name()
    tplt = \
"""\
  modport {view_name} (
{port_direction}
  );\
"""
    return tplt.format( **locals() )

  def rtlir_tr_interface_wire_decls( s, wire_decls ):
    make_indent( wire_decls, 1 )
    return '\n'.join( wire_decls )

  def rtlir_tr_interface_wire_decl( s, id_, rtype, array_type, dtype ):
    return dtype['decl'].format( **locals() ) + ' ' + array_type['decl'] + ';'

  # Definitions

  def rtlir_tr_interface_defs( s, ifc_defs ):
    return '\n'.join( ifc_defs )

  def rtlir_tr_interface_def( s, ifc_rtype, wire_defs, view_defs ):
    ifc_type_name = ifc_rtype.get_name()
    tplt = \
"""\
interface {ifc_type_name};
{wire_defs}

{view_defs}
endinterface
"""
    return tplt.format( **locals() )

  # Signal operations

  def rtlir_tr_interface_port_array_index( s, base_signal, index ):
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    return '{base_signal}.{attr}'.format( **locals() )
