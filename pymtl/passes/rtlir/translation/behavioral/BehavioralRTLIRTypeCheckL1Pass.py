#=========================================================================
# BehavioralRTLIRTypeCheckL1Pass.py
#=========================================================================
# Perform type checking on all blocks' RTLIR for a given component. This
# pass does not have a namespace to write to because it only throws an
# exception when a type error is detected.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

from pymtl                import *
from pymtl.passes         import BasePass, PassMetadata
from pymtl.passes.utility import freeze
from pymtl.passes.rtlir.translation.behavioral.BehavioralRTLIR import *
from pymtl.passes.rtlir.translation.behavioral.BehavioralRTLIRTypeL1 import *

from errors             import PyMTLTypeError

class BehavioralRTLIRTypeCheckL1Pass( BasePass ):

  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """perform type checking on all RTLIR in rtlir_upblks"""

    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()

    visitor = BehavioralRTLIRTypeCheckVisitorL1( m, s.type_env )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# BehavioralRTLIRTypeCheckVisitorL1
#-------------------------------------------------------------------------
# Visitor that performs type checking on RTLIR

class BehavioralRTLIRTypeCheckVisitorL1( BehavioralRTLIRNodeVisitor ):

  def __init__( s, component, type_env ):
    s.component = component

    s.type_env = type_env

    #---------------------------------------------------------------------
    # The expected evaluation result types for each type of RTLIR node
    #---------------------------------------------------------------------

    s.type_expect = {}

    lhs_types = ( Signal, Array )

    s.type_expect[ 'Assign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/array!' ),
      'value' : ( (Const,Signal), 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'Attribute' ] = {
      'value':( ( Module ), 'the base of an attribute must be a module!' )
    }
    s.type_expect[ 'Index' ] = {
      'value':( (Array, Signal, Const),\
        'the base of an index must be an array, signal, or constant!' ),
      'idx':( (Const, Signal), 'index must be a constant expression or a signal!' )
    }
    s.type_expect[ 'Slice' ] = {
      'value':( Signal, 'the base of a slice must be a signal!' ),
      'lower':( Const, 'upper of slice must be a constant expression!' ),
      'upper':( Const, 'lower of slice must be a constant expression!' )
    }

  def enter( s, blk, rtlir ):
    """ entry point for RTLIR type checking """
    s.blk     = blk

    # s.globals contains a dict of the global namespace of the module where
    # blk was defined
    s.globals = blk.func_globals

    # s.closure contains the free variables defined in an enclosing scope.
    # Basically this is the model instance s.
    s.closure = {}

    for i, var in enumerate( blk.func_code.co_freevars ):
      try: 
        s.closure[ var ] = blk.func_closure[ i ].cell_contents
      except ValueError: 
        pass

    s.visit( rtlir )

  # Override the default visit()
  def visit( s, node ):
    node_name = node.__class__.__name__
    method = 'visit_' + node_name
    func = getattr( s, method, s.generic_visit )

    # First visit (type check) all child nodes
    for field in node.__dict__.keys():
      value = node.__dict__[ field ]
      if isinstance( value, list ):
        for item in value:
          if isinstance( item, BaseBehavioralRTLIR ):
            s.visit( item )
      elif isinstance( value, BaseBehavioralRTLIR ):
        s.visit( value )

    # Then verify that all child nodes have desired types
    try:
      # Check the expected types of child nodes
      for field, type_rule in s.type_expect[node_name].iteritems():
        value = node.__dict__[ field ]
        target_type = type_rule[ 0 ]
        exception_msg = type_rule[ 1 ]

        if eval( 'not isinstance( value.Type, target_type )' ):
          raise PyMTLTypeError( s.blk, node, exception_msg )

    except PyMTLTypeError:
      raise
    except:
      # This node does not require type checking on child nodes
      pass

    # Finally call the type check function
    func( node )

  # Override the default generic_visit()
  def generic_visit( s, node ):
    node.Type = None

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    # RHS should have the same type as LHS
    rhs_type = node.value.Type
    lhs_type = node.target.Type

    if not lhs_type( rhs_type ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'Unagreeable types between assignment LHS and RHS!'
      )

    node.Type = None

  #-----------------------------------------------------------------------
  # visit_Base
  #-----------------------------------------------------------------------

  def visit_Base( s, node ):
    # Mark this node as having type module
    # In L1 the `s` top component is the only possible base
    node.Type = Module( node.base, s.type_env[freeze( node.base )].type_env )

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  def visit_Number( s, node ):
    # By default, number literals have bitwidth of 32
    node.Type = Const( True, 32, node.value )

  #-----------------------------------------------------------------------
  # visit_Bitwidth
  #-----------------------------------------------------------------------

  def visit_Bitwidth( s, node ):
    nbits = node.nbits
    Type = node.value.Type

    # We do not check for bitwidth mismatch here because the user should
    # be able to *explicitly* convert signals/constatns to different bitwidth.

    if not isinstance( Type, ( Signal, Const ) ):
      # Array, Bool, Module cannot have bitwidth
      raise PyMTLTypeError(
        s.blk, node.ast, 'bitwidth does not apply to' + str(Type) + '!'
      )

    if isinstance( Type, Signal ):
      node.Type = Signal( nbits )

    elif isinstance( Type, Const ):
      node.Type = Const( Type.is_static, nbits, Type.value )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    # node.value should subclass RTLIRType.BaseAttr
    # Make sure node.value has an attribute named attr
    if not node.attr in node.value.Type.obj.__dict__:
      raise PyMTLTypeError(
        s.blk, node.ast, 'class {base} does not have attribute {attr}!'.\
        format( 
          base = node.value.Type.obj.__class__.__name__,
          attr = node.attr
        )
      )

    # value.attr has the type that is specified in the type environment
    attr_obj = node.value.Type.obj.__dict__[ node.attr ]
    node.Type = node.value.Type.type_env[ freeze( attr_obj ) ]

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    if isinstance( node.idx.Type, Const ):
      # If the index is a constant expression, it is possible to do static
      # range check.
      # Check whether the index is in the range of the array
      if node.idx.Type.is_static:
        if isinstance( node.value.Type, Array ):
          if not ( 0 <= node.idx.Type.value <= node.value.Type.length ):
            raise PyMTLTypeError(
              s.blk, node.ast, 'array index out of range!'
            )

        else:
          if not ( 0 <= node.idx.Type.value <= node.value.Type.nbits ):
            raise PyMTLTypeError(
              s.blk, node.ast, 'bit index out of range!'
            )

    else:
      # This is a Signal type. No further static checking can be done
      pass

    if isinstance( node.value.Type, Array ):
      # The result type should be array.Type
      node.Type = node.value.Type.Type
    else:
      # Single bit signal
      node.Type = Signal( 1 )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    # Check slice range only if lower and upper bounds are static
    if node.lower.Type.is_static and node.upper.Type.is_static:
      lower_val = node.lower.Type.value
      upper_val = node.upper.Type.value
      signal_nbits = node.value.Type.nbits

      # upper bound must be strictly larger than the lower bound
      if ( lower_val >= upper_val ):
        raise PyMTLTypeError(
          s.blk, node.ast,
          'the upper bound of a slice must be larger than the lower bound!'
        )

      # upper & lower bound should lie in the bit width of the signal
      if not ( 0 <= lower_val < upper_val <= signal_nbits ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'upper/lower bound of slice out of width of signal!'
        )

      node.Type = Signal( upper_val - lower_val )

    else:
      node.Type = Signal( 0 )
