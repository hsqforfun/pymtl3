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
from pymtl.passes.rtlir.utility import freeze
from pymtl.passes.rtlir.RTLIRType import *

from BehavioralRTLIR import *
from BehavioralRTLIRTypeCheckL4Pass import BehavioralRTLIRTypeCheckVisitorL4
from errors             import PyMTLTypeError

class BehavioralRTLIRTypeCheckL5Pass( BasePass ):

  def __call__( s, m ):
    """perform type checking on all RTLIR in rtlir_upblks"""

    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()

    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL5(
      m,
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

  def __init__( s, component, freevars, tmpvars ):

    super( BehavioralRTLIRTypeCheckVisitorL5, s ).\
        __init__( component, freevars, tmpvars )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------
  # Only static constant expressions can be the index of component arrays

  def visit_Index( s, node ):

    if isinstance( node.value.Type, Array ) and\
       isinstance( node.value.Type.get_sub_type(), Component ):

      if not hasattr( node, '_value' ):

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

    # Attributes of subcomponent can only access ports

    if isinstance( node.value.Type, Component ) and\
       not node.value.Type.get_name() == s.component.__class__.__name__:

      if not node.value.Type.has_property( node.attr ):
        raise PyMTLTypeError(
          s.blk, node.ast,
          'Component {} does not have attribute {}!'.format(
            node.value.Type.get_name(), node.attr ) )

      prop = node.value.Type.get_property( node.attr )

      if not is_of_type( prop, Port ):
        raise PyMTLTypeError(
          s.blk, node.ast,
          '{} is not a port of subcomponent {}!'.format(
            node.attr, node.value.Type.get_name() ) )

      node.Type = prop

    else:

      super( BehavioralRTLIRTypeCheckVisitorL5, s ).visit_Attribute( node )

    if isinstance( node.value, Component ):
      s._hierarhcy_level += 1

    if s._hierarhcy_level > 2:
      raise PyMTLTypeError(
        s.blk, node.ast,
        'corss-hierarhcy reference: attribute {} of {} accessed in {}.'.format(
          node.attr, node.value, s.component
        )
      )

    if _cleanup_level: delattr( s, '_hierarhcy_level' )
