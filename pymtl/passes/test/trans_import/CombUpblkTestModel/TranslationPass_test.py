from pymtl import *
from pymtl.passes.test.trans_import.Verify import Verify
from hypothesis import given, settings, HealthCheck, unlimited, seed
from copy       import deepcopy
import hypothesis.strategies as st
import random

@st.composite
def CombinationalUpblkStrategy( draw ):

  def indent( stmts, level = 1 ):
    ''' add indent to a list of stmts '''
    padding = ' ' * 2 * level
    lines = ( line for stmt in stmts for line in stmt.splitlines() )
    return '\n'.join( padding + line for line in lines )

  def cmp_term( expr_l, cmpop, expr_r ):
    return '({expr_l} {cmpop} {expr_r})'.format( **locals() )

  def if_cond( cmp_terms ):
    ret = 'if {}:'

    ret = ret.format( ' or '.join( cmp_terms ) )

    return ret

  upblk_tmpl = """
from pymtl import *

class CombUpblkTestModel( RTLComponent ):

  def construct( s ):
    
    s.in_   = [ InVPort( Bits32 ) for _x in xrange( {in_nports} ) ]
    s.out   = [ OutVPort( Bits32 ) for _x in xrange( {out_nports} ) ]

    @s.update
    def upblk():
      
{upblk_body}

  def line_trace( s ):
    
    return {line_trace}
  """

  in_nports       = random.randint( 1, 10 )
  out_nports      = random.randint( 1, 10 )

  in_idx_st       = st.integers( min_value = 0, max_value = in_nports - 1 )
  out_idx_st      = st.integers( min_value = 0, max_value = out_nports - 1 )

  in_port_st      = st.builds( lambda idx: 's.in_[{}]'.format( idx ), in_idx_st )
  out_port_st     = st.builds( lambda idx: 's.out[{}]'.format( idx ), out_idx_st )

  operators_st     = st.sampled_from( [ '+', '-', '<<', '>>' ] )
  
  cmp_st          = st.sampled_from( [ '==', '!=', '<', '>' ] )

  literal_st      = st.builds( lambda n: 'Bits32({})'.format( n ),
        st.integers( min_value = 1, max_value = 1024 ) 
      )

  lhs_st          = st.one_of( out_port_st )
  rhs_st          = st.one_of( literal_st, in_port_st )

  expr_deferred_st= st.deferred( lambda: expr_st )

  expr_st         = st.one_of( rhs_st, st.builds(
    lambda exprl, op, exprr: '{exprl} {op} {exprr}'.format( **locals() ),
    expr_deferred_st, operators_st, expr_deferred_st
    ) )

  cmp_term_st     = st.builds( cmp_term, expr_st, cmp_st, expr_st )

  if_cond_st      = st.builds( if_cond, 
      st.lists( cmp_term_st, min_size = 1, max_size = 3 )
    )

  stmts_deferred_st = st.deferred( lambda: upblk_stmts_st )

  upblk_assign_st   = st.builds( lambda lhs, expr: 
          '{lhs} = {expr}'.format( **locals() ), lhs_st, expr_st 
      )

  upblk_if_st       = st.builds( lambda cond, stmts:
      '{}\n{}'.format( cond, stmts ), if_cond_st, stmts_deferred_st )

  upblk_if_else_st  = st.builds( lambda cond, stmts, stmts_else:
        '{}\n{}\nelse:\n{}'.format( cond, stmts, stmts_else ), 
        if_cond_st, stmts_deferred_st, stmts_deferred_st
      )

  # upblk_stmts should be a list of stmts

  upblk_stmts_st    = st.builds( indent, st.lists( 
          upblk_assign_st | upblk_if_st | upblk_if_else_st, 
          min_size = 1, max_size = 4
    ) )

  upblk_body = indent( [ draw( upblk_stmts_st ) ], level = 2 )

  # Generate test_vector

  test_vector = [ 'in_' ]

  for n_cases in xrange( 1 ):
    vector = []
    for idx in xrange( in_nports ):
      vector.append( Bits32( random.randint( 0, 256 ) ) )
    test_vector.append( [ vector ] )

  # Generate line trace

  line_trace = "'in_:{}, out:{}'.format(s.in_, s.out)"

  return ( upblk_tmpl.format( **locals() ), deepcopy( test_vector ) ) 

@given( CombinationalUpblkStrategy() )
@settings( timeout = unlimited, deadline = None,
  suppress_health_check = [ HealthCheck.too_slow ] ) 
def test_comb_upblk_trans_st( comb_upblk ):

  py_src, test_vector = comb_upblk

  with open( 'CombUpblkTestModel.py', 'w' ) as output_file:
    output_file.write( py_src )

  print '================================================================'
  print 'Running Verify( CombUpblkTestModel, {} )'.format(test_vector)
  print 'py_src: '
  print py_src

  Verify( 'CombUpblkTestModel', test_vector, verbosity = 'normal' )

if __name__ == '__main__':
  test_comb_upblk_trans_st()