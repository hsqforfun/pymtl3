#=========================================================================
# StructuralRTLIRGenL3Pass.py
#=========================================================================
# This pass generates the structural RTLIR of a given component.
#
# Author : Peitian Pan
# Date   : Apr 3, 2019

from StructuralRTLIRGenL2Pass import StructuralRTLIRGenL2Pass
from ..RTLIRType import *
from StructuralRTLIRSignalExpr import CurComp

class StructuralRTLIRGenL3Pass( StructuralRTLIRGenL2Pass ):

  def __call__( s, top ):

    super( StructuralRTLIRGenL3Pass, s ).__call__( top )

  #-----------------------------------------------------------------------
  # contains
  #-----------------------------------------------------------------------
  # At L3 not all signals have direct correspondance to `s.connect`
  # statements because of interfaces. Therefore we need to check if `obj`
  # is some parent of `signal`.

  # Override
  def contains( s, obj, signal ):

    if obj == signal: return True

    while not isinstance( signal, CurComp ):
      signal = signal.get_base()
      if obj == signal:
        return True

    return False
