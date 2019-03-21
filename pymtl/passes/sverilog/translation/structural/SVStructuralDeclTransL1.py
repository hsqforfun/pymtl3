#=========================================================================
# SVSignalDeclTransL1.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural import StructuralDeclTransL1

class SVStructuralDeclTransL1( StructuralDeclTransL1 ):

  @staticmethod
  def rtlir_tr_port_decls( port_decls ):
    make_indent( port_decls, 1 )
    return ',\n'.join( port_decls )

  @staticmethod
  def rtlir_tr_port_decl( direction, name, Type ):
    return '{} {} {} {}'.format(
      direction, Type['dtype'], Type['vec_size'], name
    )
