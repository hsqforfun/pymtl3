#=========================================================================
# SVBehavioralTranslatorL5.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods.
#
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL5\
    import BehavioralTranslatorL5
from pymtl.passes.rtlir.RTLIRType import *

from SVBehavioralTranslatorL4 import BehavioralRTLIRToSVVisitorL4

class SVBehavioralTranslatorL5( BehavioralTranslatorL5 ):

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_decl( s, m, upblk, rtlir_upblk ):
    visitor = BehavioralRTLIRToSVVisitorL5( m )
    return visitor.enter( upblk, rtlir_upblk )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL5
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL5( BehavioralRTLIRToSVVisitorL4 ):

  def __init__( s, component ):

    super( BehavioralRTLIRToSVVisitorL5, s ).__init__( component )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):

    if isinstance( node.value.Type, Module ):

      idx = node.idx.Type.value
      value = s.visit( node.value )

      return '{value}_{idx}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL5, s ).visit_Index( node )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    if not isinstance( node.value, Base ) and\
           isinstance( node.value.Type, Module ):

      value = s.visit( node.value )
      attr = node.attr

      return '{value}${attr}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL5, s ).visit_Attribute( node )
