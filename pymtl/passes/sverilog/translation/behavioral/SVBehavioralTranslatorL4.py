#=========================================================================
# SVBehavioralTranslatorL4.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods defined
# in UpblkTrans.py.
#
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL4\
    import BehavioralTranslatorL4
from pymtl.passes.rtlir.RTLIRType import *

from SVBehavioralTranslatorL3 import BehavioralRTLIRToSVVisitorL3,\
                                     SVBehavioralTranslatorL3

class SVBehavioralTranslatorL4(
    SVBehavioralTranslatorL3, BehavioralTranslatorL4 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL4

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL4
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL4( BehavioralRTLIRToSVVisitorL3 ):

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    if isinstance( node.value, InterfaceView ):

      value = s.visit( node.value )
      attr = node.attr

      return '{value}_{attr}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL4, s ).visit_Attribute( node )
