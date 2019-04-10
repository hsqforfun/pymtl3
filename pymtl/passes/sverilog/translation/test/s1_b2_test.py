#=========================================================================
# s1_b2_test.py
#=========================================================================
# Pure behavioral tests with value ports and no connections
# Behavioral L2: if, for, temporary variables, bool, comparison

import pytest

from pymtl import *
from pymtl.passes.utility.test_utility import *
from pymtl.passes.sverilog.import_.helpers import pymtl_name

from ..SVRTLIRTranslator import mk_SVRTLIRTranslator
from ..TranslationPass   import mk_TranslationPass
from ....                import SimpleImportPass

def local_do_test( m ):

  m_copy = copy.deepcopy( m )

  # Convert the input data into correct type

  for key, value in m._input_data.iteritems():
    Type = value[1]

    for idx, data in enumerate( value[0] ):
      value[0][idx] = Type( data )

  # Generate reference output

  output_val = gen_sim_reference( m, m._input_data, m._outport_types )

  # Generate translation pass with the given structural & behavioral levels

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTranslator, 1, 2
  )

  # Mangle the names of ports because the import pass might have done the
  # same

  _input_data, _outport_types, _output_val = {}, {}, {}
  for name, value in m._input_data.iteritems():
    _input_data[ pymtl_name( name ) ] = value
  for name, value in m._outport_types.iteritems():
    _outport_types[ pymtl_name( name ) ] = value
  for name, value in output_val.iteritems():
    _output_val[ pymtl_name( name ) ] = value

  # Verfiy the imported model against the reference output

  run_sim_reference_test(
    m_copy, _input_data, _outport_types, _output_val,
    translation_pass, SimpleImportPass
  )

  # Calling `finalize()` is necessary to immediately destroy the cached
  # dynamic library in CFFI

  m_copy._pass_simple_import.imported_model.finalize()
  del m_copy
  del m

def test_upblk_if1( do_test ):

  class TestComponent( Component  ):

    def construct( s ):

      s.in_2 = [ [ [ InVPort( Bits1 ) for _ in xrange(2) ] for _ in xrange(1) ] for _ in xrange(2) ]
      s.out1 = [ [ OutVPort( Bits2 ) for _ in xrange(2) ] for _ in xrange(3) ]

      # Output bitwidth = 16

      @s.update
      def if1():
        if s.in_2[0][0][0]:
          s.out1[0][0] = Bits2( 1 )
        else:
          s.out1[0][0] = 0

        if s.in_2[0][0][1] == s.in_2[1][0][1]:
          s.out1[0][1] = s.in_2[1][0][1] & s.in_2[0][0][1]
          s.out1[1][0] = s.in_2[0][0][1] | s.in_2[1][0][1]
        else:
          s.out1[0][1] = 0
          s.out1[1][0] = 0

        if s.in_2[1][0][1] <= s.in_2[0][0][0]:

          if s.in_2[1][0][1] & s.in_2[1][0][0]:
            s.out1[1][1] = Bits1(1)
            s.out1[2][0] = 1
          else:
            s.out1[1][1] = Bits1(0)
            if Bits1(1) + 0:
              s.out1[2][0] = 1
            else:
              s.out1[2][0] = 0

          s.out1[1][1] = 10
        else:
          s.out1[1][1] = Bits1(0)
          s.out1[2][0] = Bits1(0)
          s.out1[2][1] = 1

  m = TestComponent()

  m._input_data = {
      'in_2[0][0][0]' : ([0], Bits1),
      'in_2[0][0][1]' : ([0], Bits1),
      'in_2[1][0][0]' : ([0], Bits1),
      'in_2[1][0][1]' : ([0], Bits1),
  }

  m._outport_types = {
      'out1[0][0]' : Bits2,
      'out1[0][1]' : Bits2,
      'out1[1][0]' : Bits2,
      'out1[1][1]' : Bits2,
      'out1[2][0]' : Bits2,
      'out1[2][1]' : Bits2,
  }

  do_test( m )

def test_upblk_assign2( do_test ):

  class TestComponent( Component  ):

    def construct( s ):
      
      Type = Bits1

      s.in_0 = InVPort( Bits1 )
      s.out0 = OutVPort( Bits2 )

      # Output bitwidth = 16

      @s.update
      def connection():
        s.out0[0:1] = Type( 1 )
        s.out0[1:2] = Bits1( 0 )

  m = TestComponent()

  m._input_data = { 'in_0': ([1], Bits1) }

  m._outport_types = { 'out0': Bits2 }

  do_test( m )
