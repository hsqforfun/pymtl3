#=========================================================================
# BehavioralRTLIRTypeCheckL5Pass.py
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
from BehavioralRTLIRTypeCheckL4Pass import BehavioralRTLIRTypeCheckVisitorL4
from errors             import PyMTLTypeError

class BehavioralRTLIRTypeCheckL5Pass( BasePass ):

  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """perform type checking on all RTLIR in rtlir_upblks"""

    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()

    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL5(
      m, s.type_env,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# BehavioralRTLIRTypeCheckVisitorL5
#-------------------------------------------------------------------------
# Visitor that performs type checking on RTLIR

class BehavioralRTLIRTypeCheckVisitorL5( BehavioralRTLIRTypeCheckVisitorL4 ):

  def __init__( s, component, type_env, freevars, tmpvars ):

    super( BehavioralRTLIRTypeCheckVisitorL5, s ).\
        __init__( component, type_env, freevars, tmpvars )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------
  # Only static constant expressions can be the index of component arrays

  def visit_Index( s, node ):

    if isinstance( node.value.Type, Module ):

      if not isinstance( node.idx.Type, Const ) or not node.idx.Type.is_static:

        raise PyMTLTypeError(
          s.blk, node.ast,
          'index of component array must be a static constant expression!'
        )

    super( BehavioralRTLIRTypeCheckVisitorL5, s ).visit_Index( node )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------
  # Detect cross-hierarchy reference

  def visit_Attribute( s, node ):

    if not hasattr( s, '_hierarchy_level' ):
      s._hierarhcy_level = 0
      _cleanup_level = True

    else:
      _cleanup_level = False

    super( BehavioralRTLIRTypeCheckVisitorL5, s ).visit_Attribute( node )

    if isinstance( node.value, Module ):
      s._hierarhcy_level += 1

    if s._hierarhcy_level > 2:
      raise PyMTLTypeError(
        s.blk, node.ast,
        'corss-hierarhcy reference: attribute {} of {} accessed in {}.'.format(
          node.attr, node.value, s.component
        )
      )

    if _cleanup_level: delattr( s, '_hierarhcy_level' )
