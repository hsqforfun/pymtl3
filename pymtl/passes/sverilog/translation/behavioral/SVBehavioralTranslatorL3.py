#=========================================================================
# SVBehavioralTranslatorL3.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods defined
# in UpblkTrans.py.
#
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL3\
    import BehavioralTranslatorL3
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl.passes.rtlir.RTLIRType import *

from SVBehavioralTranslatorL2 import BehavioralRTLIRToSVVisitorL2,\
                                     SVBehavioralTranslatorL2

class SVBehavioralTranslatorL3(
    SVBehavioralTranslatorL2, BehavioralTranslatorL3 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL3

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL3
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL3( BehavioralRTLIRToSVVisitorL2 ):

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):

    raise NotImplementedError()

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    if isinstance( node.value.Type, Signal ):

      if isinstance( node.value.Type, Const ):
        assert False,\
            'attritbute {} of constants {} are not supported!'.format(
                node.attr, node.value
            )

      if isinstance( node.value.Type.get_dtype(), Struct ):

        value = s.visit( node.value )
        attr = node.attr

        return '{value}.{attr}'.format( **locals() )

    return super( BehavioralRTLIRToSVVisitorL3, s ).visit_Attribute( node )
