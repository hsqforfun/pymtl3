#=========================================================================
# BehavioralRTLIRTypeCheckL4Pass.py
#=========================================================================
# Perform type checking on all blocks' RTLIR for a given component. This
# pass does not have a namespace to write to because it only throws an
# exception when a type error is detected.
#
# Author : Peitian Pan
# Date   : March 30, 2019

from pymtl.passes         import BasePass, PassMetadata
from pymtl.passes.utility import freeze
from pymtl.passes.rtlir.RTLIRType import *

from BehavioralRTLIR import *
from BehavioralRTLIRTypeCheckL3Pass import BehavioralRTLIRTypeCheckVisitorL3
from errors             import PyMTLTypeError

class BehavioralRTLIRTypeCheckL4Pass( BasePass ):

  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """perform type checking on all RTLIR in rtlir_upblks"""

    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()

    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL4(
      m, s.type_env,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# BehavioralRTLIRTypeCheckVisitorL4
#-------------------------------------------------------------------------
# Visitor that performs type checking on RTLIR

class BehavioralRTLIRTypeCheckVisitorL4( BehavioralRTLIRTypeCheckVisitorL3 ):

  def __init__( s, component, type_env, freevars, tmpvars ):

    super( BehavioralRTLIRTypeCheckVisitorL4, s ).\
        __init__( component, type_env, freevars, tmpvars )

    s.type_expect[ 'Attribute' ] = {
      'value':( (Module, Struct, Interface),
        'the base of an attribute must be one of: module, struct, interface!' )
    }

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):

    if isinstance( node.value.Type, Interface ):

      if not isinstance( node.idx.Type, Const ) or not node.idx.Type.is_static:

        raise PyMTLTypeError(
          s.blk, node.ast,
          'index of interface array must be a static constant expression!'
        )

    else:

      super( BehavioralRTLIRTypeCheckVisitorL4, s ).visit_Index( node )
