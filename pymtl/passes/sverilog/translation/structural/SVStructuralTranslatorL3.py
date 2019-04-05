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
    make_indent( ifc_decls, 1 )
    return ',\n'.join( ifc_decls )

  def rtlir_tr_interface_port_decl( s, ifc_view_name, ifc_view_rtype ):
    ifc_name = ifc_view_rtype.get_interface().get_name()
    ifc_view_type_name = ifc_view_rtype.get_name()
    return '{ifc_name}.{ifc_view_type_name} {ifc_view_name}'.format(**locals())

  def rtlir_tr_interface_view_port_directions( s, directions ):
    return directions
    # make_indent( directions, 2 )
    # return ',\n'.join( directions )

  def rtlir_tr_interface_view_port_direction( s, port_name, port_rtype ):
    return port_rtype.get_direction() + ' ' + port_name

  def rtlir_tr_interface_view_decls( s, view_decls ):
    return '\n'.join( view_decls )

  def rtlir_tr_interface_view_decl( s, view_rtype, directions ):

    view_name = view_rtype.get_name()
    make_indent( directions, 2 )
    port_direction = ',\n'.join( directions )
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

  def rtlir_tr_interface_wire_decl( s, name, rtype, dtype ):
    return dtype['decl'].format( **locals() ) + ';'

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

  def rtlir_tr_interface_attr( s, base_signal, attr ):
    return '{base_signal}.{attr}'.format( **locals() )
