#=========================================================================
# s1_b0_hypothesis_test.py
#=========================================================================
# Tests with value ports and connections, no upblks.

import pytest, sys, linecache, os

import hypothesis.strategies as st
from   hypothesis import given, settings, HealthCheck, unlimited, seed,\
                         Verbosity, PrintSettings

from pymtl import *
from pymtl.passes.utility.test_utility import *
from pymtl.passes.sverilog.import_.helpers import pymtl_name

from ..SVRTLIRTranslator import mk_SVRTLIRTranslator
from ..TranslationPass   import mk_TranslationPass
from ....                import SimpleImportPass

def local_do_test( m ):

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTranslator, 1, 0
  )

  # import pdb
  # pdb.set_trace()

  try:

    for key, value in m._input_data.iteritems():
      Type = value[1]

      for idx, data in enumerate( value[0] ):
        value[0][idx] = Type( data )

    output_val =\
      gen_sim_reference( m, m._input_data, m._outport_types )
    
    print '---------------------------------------------'
    print output_val
    print '---------------------------------------------'

    _input_data, _outport_types, _output_val = {}, {}, {}
    for name, value in m._input_data.iteritems():
      _input_data[ pymtl_name( name ) ] = value
    for name, value in m._outport_types.iteritems():
      _outport_types[ pymtl_name( name ) ] = value
    for name, value in output_val.iteritems():
      _output_val[ pymtl_name( name ) ] = value

    run_sim_reference_test(
      m._unelaborated, _input_data, _outport_types, _output_val,
      translation_pass, SimpleImportPass
    )

    m._unelaborated._pass_simple_import.imported_model.finalize()
    del m._unelaborated
    del m

  except Exception as e:

    assert False, e.args

  print "Test passed!"
  print '============================================='

#-------------------------------------------------------------------------
# array_type
#-------------------------------------------------------------------------

@st.composite
def array_type( draw, obj_type ):

  obj = draw( obj_type )
  obj_str = obj[0]
  length = draw( st.integers( min_value = 1, max_value = 10 ) )
  Type = { 'Type' : 'Array', 'length' : length, 'subtype' : obj[1] }

  return\
    (
      '[ {obj_str} for _ in xrange({length}) ]'.format( **locals() ),
      Type
    )

#-------------------------------------------------------------------------
# array_data
#-------------------------------------------------------------------------

@st.composite
def array_data( draw, name, signal_type, n_cases ):

  data = {}

  for i in xrange( signal_type['length'] ):

    data.update( draw(
      signal_data(
        name=name+'[{}]'.format(i),
        signal_type=signal_type['subtype'],
        n_cases=n_cases
      ) )
    )

  return data

#-------------------------------------------------------------------------
# vector_type
#-------------------------------------------------------------------------

@st.composite
def vector_type( draw, direction ):

  width = draw( st.integers( min_value = 1, max_value = 128 ) )
  Bits_type = eval('Bits{}'.format(width))
  Type = { 'Type' : 'Vector', 'nbits' : width, 'Bits' : Bits_type }

  return\
    (
      '{direction}( Bits{width} )'.format( **locals() ),
      Type
    )

#-------------------------------------------------------------------------
# vector_data
#-------------------------------------------------------------------------

@st.composite
def vector_data( draw, name, signal_type, n_cases ):

  values = []
  for i in xrange( n_cases ):
    values.append( draw( st.integers(
      min_value = 0, max_value = 2**signal_type['nbits']-1
    ) ) )

  Bits_type = eval('Bits{}'.format(signal_type['nbits']))

  return { name : ( values, Bits_type ) }
  # return { name : value }

#-------------------------------------------------------------------------
# signal
#-------------------------------------------------------------------------

def signal( direction ):

  return st.one_of(
    array_type( st.deferred( lambda: signal( direction=direction ) ) ),
    vector_type( direction=direction )
  )

#-------------------------------------------------------------------------
# signal_data
#-------------------------------------------------------------------------

@st.composite
def signal_data( draw, name, signal_type, n_cases ):

  if signal_type['Type'] == 'Array':

    return draw( array_data( name=name, signal_type=signal_type,
      n_cases=n_cases ) )

  elif signal_type['Type'] == 'Vector':

    return draw( vector_data( name=name, signal_type=signal_type,
      n_cases=n_cases ) )

  else: assert False

#-------------------------------------------------------------------------
# inport_data
#-------------------------------------------------------------------------

@st.composite
def inport_data( draw, signal_type ):
  pass

#-------------------------------------------------------------------------
# inport
#-------------------------------------------------------------------------

@st.composite
def inport( draw, port_num, port_type=signal( direction="InVPort" ) ):

  inport_type = draw( port_type )
  inport_type_str = inport_type[0]
  Type = inport_type[1]

  return\
    (
      '    s.in_{port_num} = {inport_type_str}'.format( **locals() ),
      Type
    )

#-------------------------------------------------------------------------
# outport
#-------------------------------------------------------------------------

@st.composite
def outport( draw, port_num, port_type=signal( direction="OutVPort" ) ):

  outport_type = draw( port_type )
  outport_type_str = outport_type[0]
  Type = outport_type[1]

  return\
    (
      '    s.out{port_num} = {outport_type_str}'.format( **locals() ),
      Type
    )

@st.composite
def vector_self( draw, signal_type ):

  return ( '', signal_type )

@st.composite
def vector_slice( draw, signal_type ):

  nbits = signal_type['nbits']

  start = draw( st.integers( min_value = 0, max_value = nbits-1 ) )
  stop  = draw( st.integers( min_value = start+1, max_value = nbits ) )

  Type = { 'Type' : 'Vector', 'nbits' : stop-start }

  rest = draw( signal_exp( signal_type = Type ) )
  rest_str = rest[0]

  return\
    (
      '[{start}:{stop}]{rest_str}'.format( **locals() ),
      rest[1]
    )

@st.composite
def vector_index( draw, signal_type ):

  nbits = signal_type['nbits']

  idx = draw( st.integers( min_value = 0, max_value = nbits-1 ) )

  Type = { 'Type' : 'Vector', 'nbits' : 1 }

  rest = draw( signal_exp( signal_type = Type ) )
  rest_str = rest[0]

  return\
    (
      '[{idx}]{rest_str}'.format( **locals() ),
      rest[1]
    )

@st.composite
def signal_exp( draw, signal_type ):

  if signal_type['Type'] == 'Array':

    array_idx = draw( st.integers(
      min_value = 0, max_value = signal_type['length']-1
    ) )

    rest = draw( st.deferred( lambda: signal_exp( signal_type['subtype'] ) ) )

    return\
      (
        '[{}]{}'.format( array_idx, rest[0] ),
        rest[1]
      )

  elif signal_type['Type'] == 'Vector':

    return draw( st.one_of(
      vector_self( signal_type=signal_type ),
      vector_slice( signal_type=signal_type ),
      vector_index( signal_type=signal_type )
    ) )

  else: assert False

#-------------------------------------------------------------------------
# S1_B0_ComponentStrategy
#-------------------------------------------------------------------------

@st.composite
def S1_B0_ComponentStrategy( draw ):

  def bit_blast( name, Type, result ):

    if Type['Type'] == 'Array':

      for i in xrange( Type['length'] ):
        bit_blast( name+'[{}]'.format(i), Type['subtype'], result )
    
    elif Type['Type'] == 'Vector':

      result.append( { 'name' : name, 'nbits' : Type['nbits'], 'cur':0 } )

    else: assert False

  def gen_port_type( name, Type, results ):

    if Type['Type'] == 'Array':

      for i in xrange(Type['length']):
        gen_port_type( name+'[{}]'.format(i), Type['subtype'], results )

    elif Type['Type'] == 'Vector':

      Bits_type = eval('Bits{}'.format(Type['nbits']))

      results[ name ] = Bits_type

    else: assert False

  def connect( expr, cur_idx, outbits, conns ):

    if (cur_idx >= len(outbits)): return cur_idx

    tplt = '    s.connect( {in_expr}, {out_expr} )'

    expr_name = expr[0]
    expr_nbits = expr[1]['nbits']

    if outbits[cur_idx]['cur'] + expr_nbits <= outbits[cur_idx]['nbits']:

      in_expr = expr_name
      out_expr = outbits[cur_idx]['name']+'[{}:{}]'.format(
        outbits[cur_idx]['cur'], outbits[cur_idx]['cur']+expr_nbits
      )
      outbits[cur_idx]['cur'] += expr_nbits

      conns.append( tplt.format( **locals() ) )

      return cur_idx+1 if outbits[cur_idx]['cur'] == outbits[cur_idx]['nbits']\
                     else cur_idx

    cur_expr_base = 0

    while expr_nbits > 0 and cur_idx < len(outbits):

      if outbits[cur_idx]['cur'] + expr_nbits <= outbits[cur_idx]['nbits']:

        in_expr = expr_name+'[{}:{}]'.format(
          cur_expr_base,
          cur_expr_base+expr_nbits
        )
        out_expr = outbits[cur_idx]['name']+'[{}:{}]'.format(
          outbits[cur_idx]['cur'], outbits[cur_idx]['cur']+expr_nbits
        )

        outbits[cur_idx]['cur'] += expr_nbits
        cur_expr_base += expr_nbits
        expr_nbits -= expr_nbits

        conns.append( tplt.format( **locals() ) )

        return cur_idx+1 if outbits[cur_idx]['cur'] == outbits[cur_idx]['nbits']\
                       else cur_idx

      out_len = outbits[cur_idx]['nbits'] - outbits[cur_idx]['cur']
      in_expr =\
        expr_name + '[{}:{}]'.format( cur_expr_base, cur_expr_base+out_len )
      out_expr = outbits[cur_idx]['name']+'[{}:{}]'.format(
        outbits[cur_idx]['cur'], outbits[cur_idx]['nbits']
      )

      conns.append( tplt.format( **locals() ) )

      outbits[cur_idx]['cur'] = outbits[cur_idx]['nbits']
      cur_expr_base += out_len
      expr_nbits -= out_len
      cur_idx += 1

    return cur_idx

  component_tplt =\
"""
from pymtl import *

class TestComponent( RTLComponent ):
  
  def construct( s ):

{inport_decls}
{outport_decls}

    {signal_exprs}

    # Output bitwidth = {out_bitwidth}
    {out_signals}

{connections}

{input_data}

  def line_trace( s ):
    
    return {line_trace}
"""

  INPORT_SIGNAL_EXPR_FACTOR = 4
  
  num_inport = draw( st.integers( min_value = 1, max_value = 5 ) )
  num_outport = draw( st.integers( min_value = 1, max_value = 5 ) )

  inports = [ draw( inport( port_num=x ) ) for x in xrange( num_inport ) ]
  outports = [ draw( outport( port_num=x ) ) for x in xrange( num_outport ) ]

  # Generate port declarations

  inport_decls = '\n'.join( map( lambda port: port[0], inports ) )
  outport_decls = '\n'.join( map( lambda port: port[0], outports ) )

  # Generate input data

  n_cases = draw( st.integers( min_value = 1, max_value = 5 ) )

  inport_data = {}
  for i, _inport in enumerate(inports):
    inport_data.update( draw(
      signal_data( name='in_'+str(i), signal_type=_inport[1],
        n_cases=n_cases ) ) 
    )

  input_data = ""
  # for name, value in inport_data.iteritems():
    # input_data += '    # ' + name + ' = ' + str(value[0]) + '\n'

  outport_types = {}
  for idx, _outport in enumerate(outports):
    gen_port_type( 'out'+str(idx), _outport[1], outport_types )

  # Generate input port signal expressions

  inport_signal_exprs =\
    [ draw( signal_exp( signal_type=inports[x/INPORT_SIGNAL_EXPR_FACTOR][1] ) )\
          for x in xrange(INPORT_SIGNAL_EXPR_FACTOR*len( inports )) ]

  signal_exprs = "\n    ".join(
    map(
      lambda tpl: '# '+tpl[0]+tpl[1][0]+', width='+str(tpl[1][1]['nbits']),
      zip(
        map( lambda i: 's.in_'+str(i/INPORT_SIGNAL_EXPR_FACTOR),
          xrange( INPORT_SIGNAL_EXPR_FACTOR*num_inport ) ),
        inport_signal_exprs
      )
    )
  )

  # Do outport bit blasting

  out_bits = []
  out_bitwidth = 0
  _out_signals = []

  for idx, out in enumerate(outports):

    bit_blast( 's.out'+str(idx), out[1], out_bits )

  for out_bit in out_bits:

    out_bitwidth += out_bit['nbits']
    _out_signals.append( '# '+out_bit['name']+',width='+str(out_bit['nbits']) )

  out_signals = ''
  # out_signals = '\n    '.join( _out_signals )

  # Sequentially connect all inport signal expressions to output

  _connections = []

  _cur_idx = 0
  for idx, inport_signal_expr in enumerate(inport_signal_exprs):
    _inport_signal_expr = (
      's.in_'+str(idx/INPORT_SIGNAL_EXPR_FACTOR)+inport_signal_expr[0],
      inport_signal_expr[1]
    )
    _cur_idx = connect( _inport_signal_expr, _cur_idx, out_bits, _connections )

  # Connect the first bit of inport signal expressions to the rest of the
  # output bits to avoid 'NoDriver' errors.

  while _cur_idx < len( out_bits ):

    _inport_signal_expr = (
      's.in_0'+inport_signal_exprs[0][0],
      inport_signal_exprs[0][1]
    )

    _cur_idx = connect( _inport_signal_expr, _cur_idx, out_bits, _connections )

  connections = '\n'.join( _connections )

  # Generate line trace

  line_trace = "'{ports}'.format( {port_format} )"

  _ports =\
    map( lambda n: 'in_'+str(n), xrange(num_inport) ) +\
    map( lambda n: 'out'+str(n), xrange(num_outport) )
  _port_format = map( lambda s: 's.'+s, _ports )
  _ports = map( lambda s: s+'={}', _ports )

  ports = ', '.join( _ports )
  port_format = ', '.join( _port_format )

  line_trace = line_trace.format( **locals() )

  return ( component_tplt.format( **locals() ), inport_data, outport_types )

#-------------------------------------------------------------------------
# test_s1_b0_hypothesis
#-------------------------------------------------------------------------

@given( component_str=S1_B0_ComponentStrategy() )
@settings( deadline = None, suppress_health_check = HealthCheck.all(),
  verbosity=Verbosity.verbose, print_blob=PrintSettings.ALWAYS
)
def test_s1_b0_hypothesis( do_test, component_str ):

  component_src, input_data, outport_types = component_str

  print '============================================='
  print component_src
  print input_data

  if not os.getcwd() in sys.path:

    sys.path.append( os.getcwd() )

  with open( 'TestComponent.py', 'w' ) as output:

    output.write( component_src )

  if 'TestComponent' in sys.modules:

    linecache.checkcache()
    _TestComponent = reload( sys.modules[ 'TestComponent' ] )
    TestComponent = _TestComponent.__dict__[ 'TestComponent' ]

  else:

    from TestComponent import TestComponent

  m = TestComponent()
  m._unelaborated = TestComponent()
  m._input_data = input_data
  m._outport_types = outport_types

  do_test( m )
