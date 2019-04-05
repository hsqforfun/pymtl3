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

from SVBehavioralTranslatorL3 import BehavioralRTLIRToSVVisitorL3

class SVBehavioralTranslatorL4( BehavioralTranslatorL4 ):

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_decl( s, m, upblk, rtlir_upblk ):
    visitor = BehavioralRTLIRToSVVisitorL4( m )
    return visitor.enter( upblk, rtlir_upblk )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL4
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL4( BehavioralRTLIRToSVVisitorL3 ):

  def __init__( s, component ):

    super( BehavioralRTLIRToSVVisitorL4, s ).__init__( component )

  def visit_Attribute( s, node ):

    if isinstance( node.value, Interface ):

      value = s.visit( node.value )
      attr = node.attr

      return '{value}.{attr}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL4, s ).visit_Attribute( node )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------
  # An array of interfaces should be name-mangled to individual
  # interfaces.

  def visit_Index( s, node ):

    if isinstance( node.value.Type, Interface ):

      idx = node.idx.Type.value
      value = s.visit( node.value )
      
      return '{value}_{idx}'.format( **locals() )

    else:

      return super( BehavioralRTLIRToSVVisitorL4, s ).visit_Index( node )
