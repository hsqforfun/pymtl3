#=========================================================================
# SVBehavioralTranslatorL1.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods defined
# in UpblkTrans.py.
#
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL1\
    import BehavioralTranslatorL1
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import *
from SVBehavioralTranslatorL0 import SVBehavioralTranslatorL0

class SVBehavioralTranslatorL1(
    SVBehavioralTranslatorL0, BehavioralTranslatorL1 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL1

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_decl( s, upblk, rtlir_upblk ):
    visitor = s._get_rtlir2sv_visitor()()
    return visitor.enter( upblk, rtlir_upblk )

  def rtlir_tr_behavioral_freevars( s, freevars ):
    return '\n'.join( freevars )

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    assert isinstance( rtype, Const ),\
    '{} freevar should be a constant!'.format( id_ )
    assert isinstance( rtype.get_dtype(), Vector ),\
    '{} freevar should be a (list of) integer!'.format( id_ )
    return s.rtlir_tr_const_decl( '_fvar_'+id_, rtype, array_type, dtype, obj )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL1
#-------------------------------------------------------------------------
# Visitor that translates RTLIR to SystemVerilog for a single upblk.

class BehavioralRTLIRToSVVisitorL1( BehavioralRTLIRNodeVisitor ):

  def __init__( s ):

    # Should use enum here, but enum is a python 3 feature...
    s.NONE          = 0
    s.COMBINATIONAL = 1
    s.SEQUENTIAL    = 2
    s.upblk_type    = s.NONE

  def enter( s, blk, rtlir ):
    """ entry point for RTLIR generation """
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

    return s.visit( rtlir )

  #-----------------------------------------------------------------------
  # visit_CombUpblk
  #-----------------------------------------------------------------------
  # CombUpblk concatenates string representation of statements inside it
  # and return the result string.

  def visit_CombUpblk( s, node ):
    blk_name = node.name
    src      = []
    body     = []

    s.upblk_type = s.COMBINATIONAL

    # Add name of the upblk to this always block
    src.extend( [ 'always_comb begin : {blk_name}'.format( **locals() ) ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )

    src.extend( [ 'end' ] )

    s.upblk_type = s.NONE

    return src

  #-----------------------------------------------------------------------
  # visit_SeqUpblk
  #-----------------------------------------------------------------------
  # SeqUpblk concatenates string representation of statements inside it
  # and return the result string.

  def visit_SeqUpblk( s, node ):
    blk_name = node.name
    src      = []
    body     = []

    s.upblk_type = s.SEQUENTIAL

    # Add name of the upblk to this always block
    src.extend( [
      'always_ff @(posedge clk) begin : {blk_name}'.format( **locals() )
    ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )

    src.extend( [ 'end' ] )

    s.upblk_type = s.NONE

    return src

  #-----------------------------------------------------------------------
  # Statements
  #-----------------------------------------------------------------------
  # All statement nodes return a list of strings.

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    target        = s.visit( node.target )
    value         = s.visit( node.value )
    assignment_op = '<=' if s.upblk_type == s.SEQUENTIAL else '='

    ret = '{target} {assignment_op} {value};'.format( **locals() )

    return [ ret ]

  #-----------------------------------------------------------------------
  # visit_AugAssign
  #-----------------------------------------------------------------------

  def visit_AugAssign( s, node ):
    assert False, "AugAssign not supported at L1"

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    assert False, "If not supported at L1"

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    assert False, "For not supported at L1"

  #-----------------------------------------------------------------------
  # Expressions
  #-----------------------------------------------------------------------
  # All expression nodes return a single string.  

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  def visit_Number( s, node ):
    # Create a number without width specifier
    return str( node.value )

  #-----------------------------------------------------------------------
  # visit_BitsCast
  #-----------------------------------------------------------------------

  def visit_BitsCast( s, node ):
    # if isinstance( node.value, Number ):
    assert isinstance( node.value, Number )
    value = node.value.value
    bit_width = node.nbits
    return "{bit_width}'d{value}".format( **locals() )
    # else:
      # return s.visit( node.value )

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    assert False, "IfExp not supported at L1"

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    assert False, "UnaryOp not supported at L1"

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    assert False, "BoolOp not supported at L1"

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    assert False, "BinOp not supported at L1"

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    assert False, "Compare not supported at L1"

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    attr  = node.attr
    value = s.visit( node.value )

    if isinstance( node.value, Base ):
      # The base of this attribute node is the component 's'.
      # Example: s.out, s.STATE_IDLE
      # assert node.value.base is s.component
      ret = attr

    else:
      assert False, "sub-components and structs are not supported at L1!"

    return ret

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------
  # At L1 all indexes are bit selections

  def visit_Index( s, node ):
    idx   = s.visit( node.idx )
    value = s.visit( node.value )
    Type = node.value.Type

    # Unpacked index
    if isinstance( Type, Array ):
      subtype = Type.get_sub_type()

      if isinstance( subtype, ( Port, Wire, Const, InterfaceView ) ):
        return '{value}[{idx}]'.format( **locals() )

      else:
        return '{value}_${idx}'.format( **locals() )

    elif isinstance( Type, Signal ):

      # Packed index
      if Type.is_packed_indexable():
        return '{value}[{idx}]'.format( **locals() )

      # Bit selection
      elif isinstance( Type.get_dtype(), Vector ):
        return '{value}[{idx}]'.format( **locals() )

      else: assert False, 'internal error: unrecoganized index'

    else: assert False, 'internal error: unrecoganized index'

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------
  # Part selection

  def visit_Slice( s, node ):

    lower = s.visit( node.lower )
    value = s.visit( node.value )

    if hasattr( node.upper, '_value' ):

      upper = str( int( node.upper._value - pymtl.Bits32(1) ) )

    else:
      
      upper = s.visit( node.upper ) + '-1'

    return '{value}[{upper}:{lower}]'.format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Base
  #-----------------------------------------------------------------------

  def visit_Base( s, node ):
    return str( node.base )

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    assert False, "LoopVar not supported at L1"

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    return '_fvar_'+node.name

  #-----------------------------------------------------------------------
  # visit_TmpVar
  #-----------------------------------------------------------------------

  def visit_TmpVar( s, node ):
    assert False, "TmpVar not supported at L1"

  #-----------------------------------------------------------------------
  # visit_LoopVarDecl
  #-----------------------------------------------------------------------

  def visit_LoopVarDecl( s, node ):
    assert False, "LoopVarDecl not supported at L1"
