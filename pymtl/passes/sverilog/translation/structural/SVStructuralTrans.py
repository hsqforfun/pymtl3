#=========================================================================
# SVStructuralTrans.py
#=========================================================================

from pymtl.passes.rtlir.translation.structural import StructuralTrans

from SVStructuralDTypeTransL1 import SVStructuralDTypeTransL1 as SVDTypeTr
from SVStructuralDeclTransL1 import SVStructuralDeclTransL1 as SVDeclTr
from SVStructuralConnectionTransL1 import SVStructuralConnectionTransL1 as SVConnTr

class SVStructuralTrans( StructuralTrans, SVDTypeTr, SVDeclTr, SVConnTr ):

  def __init__( s, top ):

    super( SVStructuralTrans, s ).__init__( top )

  def translate( s ):

    super( SVStructuralTrans, s ).translate()
