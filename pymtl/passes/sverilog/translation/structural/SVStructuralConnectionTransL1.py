#=========================================================================
# SVStructuralConnectionTransL1.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural import StructuralConnectionTransL1

class SVStructuralConnectionTransL1( StructuralConnectionTransL1 ):

  @staticmethod
  def rtlir_tr_connections_self_self( connections_self_self ):
    make_indent( connections_self_self, 1 )
    return '\n'.join( connections_self_self )

  @staticmethod
  def rtlir_tr_connection_self_self( wr_signal, rd_signal ):
    return 'assign {} = {};'.format( rd_signal, wr_signal )
