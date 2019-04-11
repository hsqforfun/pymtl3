#=========================================================================
# test_utility.py
#=========================================================================
# This file provides some useful utility that might be needed by some
# test cases.
#
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest, inspect, copy

from pymtl                   import *
from pymtl.passes.PassGroups import SimpleSim, SimpleSimDumpDAG
from pclib.rtl.TestSource    import TestBasicSource as TestSource
from pclib.rtl.TestSink      import TestBasicSink   as TestSink

from pymtl.passes.rtlir.behavioral import MinBehavioralRTLIRLevel,\
                                          MaxBehavioralRTLIRLevel
from pymtl.passes.rtlir.structural import MinStructuralRTLIRLevel,\
                                          MaxStructuralRTLIRLevel

from contextlib              import contextmanager

#-------------------------------------------------------------------------
# do_test
#-------------------------------------------------------------------------
# Makes sure the tests only call the local_do_test function in their
# modules. From PyMTL v2.

@pytest.fixture
def do_test( request ):
  return request.module.local_do_test

#-------------------------------------------------------------------------
# expected_failure
#-------------------------------------------------------------------------
# This context is used to run a test case which is expected to fail and
# throwing a specific exception is the correct behavior.
# Not to be confused with pytest.xfail, which is commonly used to mark
# tests related to unimplemented functionality.

@contextmanager
def expected_failure( exception = Exception ):
  """Mark one test case as expected failure, which only passes the test
  when it throws an expected exception."""

  try:
    yield
  except exception:
    return
  except:
    raise

  raise Exception( 'expected-to-fail test unexpectedly passed!' )

#-------------------------------------------------------------------------
# gen_rtlir_translator
#-------------------------------------------------------------------------

_rtlir_translators = {}

def gen_rtlir_translator( structural_level, behavioral_level ):

  label = str( structural_level ) + str( behavioral_level )

  if label in _rtlir_translators: return _rtlir_translators[ label ]

  assert MinStructuralRTLIRLevel <= structural_level <= MaxStructuralRTLIRLevel
  assert MinBehavioralRTLIRLevel <= behavioral_level <= MaxBehavioralRTLIRLevel

  structural_tplt =\
    'from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL{0}\
       import StructuralTranslatorL{0} as _StructuralTranslator'

  behavioral_tplt =\
    'from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL{0}\
       import BehavioralTranslatorL{0} as _BehavioralTranslator'

  exec structural_tplt.format( structural_level ) in globals(), locals()
  exec behavioral_tplt.format( behavioral_level ) in globals(), locals()
  
  from pymtl.passes.rtlir.translation.RTLIRTranslator import mk_RTLIRTranslator

  _rtlir_translators[ label ] = mk_RTLIRTranslator(
    _BehavioralTranslator, _StructuralTranslator
  )

  return _rtlir_translators[ label ]

#-------------------------------------------------------------------------
# gen_translation_pass
#-------------------------------------------------------------------------

_backend_translators = {}

def gen_translation_pass( mk_pass, mk_backend_trans, structural_level,
    behavioral_level ):

  label = str( structural_level ) + str( behavioral_level )

  if label in _backend_translators:
    return mk_pass( _backend_translators[ label ] )

  rtlir_trans = gen_rtlir_translator( structural_level, behavioral_level )

  _backend_translators[ label ] =\
    mk_backend_trans(
      rtlir_trans, b_level=behavioral_level, s_level=structural_level
    )

  return mk_pass( _backend_translators[ label ] )

#-------------------------------------------------------------------------
# port_name_mangle
#-------------------------------------------------------------------------

def port_name_mangle( values, import_pass ):
  assert hasattr( import_pass, 'port_name_mangle' ),\
    'import pass {} does not have `port_name_mangle` method!'.format(
        import_pass )
  ret = {}
  for name, value in values.iteritems():
    ret[ import_pass.port_name_mangle( name ) ] = value
  return ret

#-------------------------------------------------------------------------
# gen_test_harness
#-------------------------------------------------------------------------

def gen_test_harness(
    dut, inport_types, outport_types, input_val, output_val
  ):

  class TestHarness( Component ):

    def construct( s, dut, inport_types, outport_types, input_val, output_val ):

      s.dut = dut

      # Setup test sources/sinks
      s.srcs = [
        TestSource( inport_types[inport_name], input_val[inport_name] )\
        for inport_name in input_val.keys()
      ]
      s.sinks = [
        TestSink( outport_types[outport_name], output_val[outport_name] )\
        for outport_name in output_val.keys()
      ]

      # Connect all srcs/sinks to ports of dut
      for idx, inport_name in enumerate(input_val.keys()):
        exec( 's.connect( s.srcs[idx].out, s.dut.{name} )'\
          .format( name = inport_name ) ) in globals(), locals()

      for idx, outport_name in enumerate(output_val.keys()):
        exec( 's.connect( s.sinks[idx].in_, s.dut.{name} )'\
          .format( name = outport_name ) ) in globals(), locals()

  return TestHarness(dut, inport_types, outport_types, input_val, output_val)

#-------------------------------------------------------------------------
# run_translation_reference_test
#-------------------------------------------------------------------------

def run_translation_reference_test(
    model, test_vec, TranslationPass, ImportPass
  ):

  #-----------------------------------------------------------------------
  # Parse the test vector header
  #-----------------------------------------------------------------------
  
  # We convert the readable test vector format into a dict-based
  # structure that will be used to drive the simulation.

  header = test_vec[0].split()
  types  = test_vec[1]
  test_vec = test_vec[2:]

  signal_pos = {}
  pos_signal = []

  inports, outports = [], []
  inport_types, outport_types = {}, {}

  # for idx, port_name in enumerate( header ):
    # if port_name.startswith( '*' ):
      # outports.append( port_name[1:] )
      # signal_pos[ port_name[1:] ] = idx
    # else:
      # inports.append( port_name )
      # signal_pos[ port_name ] = idx
    # pos_signal.append( port_name )

  for idx, (port_name, port_type) in enumerate( zip(header, types) ):
    if port_name.startswith( '*' ):
      outports.append( port_name[1:] )
      outport_types[ port_name[1:] ] = port_type
      signal_pos[ port_name[1:] ] = idx
    else:
      inports.append( port_name )
      inport_types[ port_name ] = port_type
      signal_pos[ port_name ] = idx
    pos_signal.append( port_name )

  input_val, output_val = {}, {}

  # Initialize the input/output value dict with empty lists

  for port_name in inports:  input_val[ port_name ]  = []
  for port_name in outports: output_val[ port_name ] = []

  for vec in test_vec:
    assert len( vec ) == ( len( inports ) + len( outports ) )
    for idx, value in enumerate( vec ):
      if pos_signal[ idx ].startswith( '*' ):
        output_val[ pos_signal[ idx ][1:] ].append( value )
      else:
        input_val[ pos_signal[ idx ] ].append( value )

  #-----------------------------------------------------------------------
  # Construct the test harness
  #-----------------------------------------------------------------------

  model.elaborate()
  model.apply( TranslationPass() )
  import_pass = ImportPass()
  model.apply( import_pass )

  dut = model._pass_simple_import.imported_model

  # I need elaborated metadata to collect the types of each port in the
  # imported component. This makes it unnecssary for users to provide
  # type information in the test vectors.

  # dut.elaborate()

  # for inport in dut.get_input_value_ports():
    # inport_types[ inport._dsl.my_name ] = inport._dsl.Type
  # for outport in dut.get_output_value_ports():
    # outport_types[ outport._dsl.my_name ] = outport._dsl.Type

  # However there is no easy way to `re-elaborate` the DUT w.r.t. a
  # new top component...

  # dut = None
  # model._pass_simple_import.imported_model = None
  # model.apply( ImportPass() )
  # dut = model._pass_simple_import.imported_model

  test_harness =\
    gen_test_harness( dut,
        port_name_mangle( inport_types, import_pass ),
        port_name_mangle( outport_types, import_pass ),
        port_name_mangle( input_val, import_pass ),
        port_name_mangle( output_val, import_pass ) )

  #-----------------------------------------------------------------------
  # Run the simulation
  #-----------------------------------------------------------------------

  # test_harness.apply( SimpleSimDumpDAG )
  test_harness.apply( SimpleSim )

  for cycle in xrange( len( test_vec ) ):
    test_harness.tick()

#-------------------------------------------------------------------------
# gen_sim_reference
#-------------------------------------------------------------------------

def gen_sim_reference( model, input_data, outport_types ):

  class RecordTestSink( Component ):

    def construct( s, Type ):

      s.in_ = InPort( Type )
      s.record = []

      @s.update
      def sink_update():
        s.record.append( copy.deepcopy(s.in_) )

    def line_trace( s ):

      return str( s.in_ )

  #-----------------------------------------------------------------------
  # Collect ports and input data
  #-----------------------------------------------------------------------
  
  n_cases = 0
  inport_types = {}
  input_val, output_val = {}, {}

  for name, value in input_data.iteritems():
    
    data = value[0]
    Type = value[1]
    n_cases = len( data )

    input_val[ name ] = data
    inport_types[ name ] = Type

  #-----------------------------------------------------------------------
  # Simulate the model to generate reference output
  #-----------------------------------------------------------------------

  class SimulationTH( Component ):

    def construct( s, dut, inport_types, outport_types, input_val ):

      s.dut = dut
      s.srcs = [ TestSource( inport_types[name], input_val[name] )\
        for name in input_val.keys()
      ]
      s.sinks = [ RecordTestSink( outport_types[name] )\
        for name in outport_types.keys()
      ]

      for idx, name in enumerate(input_val.keys()):
        exec('s.connect(s.srcs[idx].out,s.dut.{name})'.format(**locals()))\
            in globals(), locals()

      for idx, name in enumerate(outport_types.keys()):
        exec('s.connect(s.sinks[idx].in_,s.dut.{name})'.format(**locals()))\
            in globals(), locals()

  sim_th = SimulationTH( model, inport_types, outport_types, input_val )

  # sim_th.apply( SimpleSimDumpDAG )
  sim_th.apply( SimpleSim )

  output_val = {}
  for name in outport_types.keys():
    output_val[name] = []

  for i in xrange( n_cases ):
    sim_th.tick()
    for idx, name in enumerate(outport_types.keys()):
      output_val[name].append( sim_th.sinks[idx].record[-1] )

  return output_val

#-------------------------------------------------------------------------
# run_sim_reference_test
#-------------------------------------------------------------------------

def run_sim_reference_test(
    model, input_data, outport_types, output_val, TranslationPass, ImportPass
  ):

  #-----------------------------------------------------------------------
  # Collect the ports and input data
  #-----------------------------------------------------------------------

  inport_types, input_val = {}, {}

  for name, value in input_data.iteritems():

    data = value[0]
    Type = value[1]
    n_cases = len( data )

    input_val[ name ] = data
    inport_types[ name ] = Type

  #-----------------------------------------------------------------------
  # Construct the test harness
  #-----------------------------------------------------------------------

  model.elaborate()
  model.apply( TranslationPass() )
  import_pass = ImportPass()
  model.apply( import_pass )

  dut = model._pass_simple_import.imported_model

  trans_th =\
    gen_test_harness( dut,
        port_name_mangle( inport_types, import_pass ),
        port_name_mangle( outport_types, import_pass ),
        port_name_mangle( input_val, import_pass ),
        port_name_mangle( output_val, import_pass ) )

  #-----------------------------------------------------------------------
  # Run the simulation
  #-----------------------------------------------------------------------

  # trans_th.apply( SimpleSimDumpDAG )
  trans_th.apply( SimpleSim )

  for i in xrange( n_cases ):
    trans_th.tick()
