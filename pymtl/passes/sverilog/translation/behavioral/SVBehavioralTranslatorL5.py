#=========================================================================
# SVBehavioralTranslatorL5.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods.
#
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.sverilog.utility import make_indent
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL5\
    import BehavioralTranslatorL5
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import Base
from pymtl.passes.rtlir.RTLIRType import *

from SVBehavioralTranslatorL4 import BehavioralRTLIRToSVVisitorL4,\
                                     SVBehavioralTranslatorL4

class SVBehavioralTranslatorL5(
    SVBehavioralTranslatorL4, BehavioralTranslatorL5 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL5

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL5
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL5( BehavioralRTLIRToSVVisitorL4 ):

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    # Generate subcomponent attribute

    if isinstance( node.value.Type, Component ) and\
       not isinstance( node.value, Base ):
       # not node.value.Type.get_name() == s.component.__class__.__name__:

      value = s.visit( node.value )
      attr = node.attr

      return '{value}${attr}'.format( **locals() )

    return super( BehavioralRTLIRToSVVisitorL5, s ).visit_Attribute( node )
