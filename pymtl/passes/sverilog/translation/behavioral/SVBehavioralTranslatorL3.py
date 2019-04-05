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

from SVBehavioralTranslatorL2 import BehavioralRTLIRToSVVisitorL2

class SVBehavioralTranslatorL3( BehavioralTranslatorL3 ):

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_decl( s, m, upblk, rtlir_upblk ):
    visitor = BehavioralRTLIRToSVVisitorL3( m )
    return visitor.enter( upblk, rtlir_upblk )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL3
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL3( BehavioralRTLIRToSVVisitorL2 ):

  def __init__( s, component ):

    super( BehavioralRTLIRToSVVisitorL3, s ).__init__( component )

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):

    raise NotImplementedError()

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    if isinstance( node.value.Type, Struct ):

      value = s.visit( node.value )
      attr = node.attr

      return '{value}.{attr}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL3, s ).visit_Attribute( node )
