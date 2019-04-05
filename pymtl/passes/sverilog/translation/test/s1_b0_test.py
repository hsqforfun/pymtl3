#=========================================================================
# s1_b0_test.py
#=========================================================================
# Tests with value ports and connections, no upblks.

import pytest, copy

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
    mk_TranslationPass, mk_SVRTLIRTranslator, 1, 0
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

def test_port_connection1( do_test ):

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits1 )
      s.in_1 = InVPort( Bits2 )
      s.in_2 = [ [ [ InVPort( Bits1 ) for _ in xrange(2) ] for _ in xrange(1) ] for _ in xrange(2) ]
      s.in_3 = InVPort( Bits1 )
      s.in_4 = InVPort( Bits1 )
      s.out0 = OutVPort( Bits2 )
      s.out1 = [ [ OutVPort( Bits2 ) for _ in xrange(2) ] for _ in xrange(3) ]
      s.out2 = OutVPort( Bits1 )
      s.out3 = OutVPort( Bits1 )

      # Output bitwidth = 16

      s.connect( s.in_0, s.out0[0:1] )
      s.connect( s.in_0, s.out0[1:2] )
      s.connect( s.in_0, s.out1[0][0][0:1] )
      s.connect( s.in_0, s.out1[0][0][1:2] )
      s.connect( s.in_1[1:2], s.out1[0][1][0:1] )
      s.connect( s.in_1[0:1], s.out1[0][1][1:2] )
      s.connect( s.in_1[1:2], s.out1[1][0][0:1] )
      s.connect( s.in_1[0:1], s.out1[1][0][1:2] )
      s.connect( s.in_1[1:2], s.out1[1][1][0:1] )
      s.connect( s.in_1[0:1], s.out1[1][1][1:2] )
      s.connect( s.in_1[1:2], s.out1[2][0][0:1] )
      s.connect( s.in_2[0][0][0][0], s.out1[2][0][1:2] )
      s.connect( s.in_2[0][0][0], s.out1[2][1][0:1] )
      s.connect( s.in_2[0][0][0], s.out1[2][1][1:2] )
      s.connect( s.in_2[0][0][0], s.out2[0:1] )
      s.connect( s.in_3, s.out3[0:1] )

  m = TestComponent()

  m._input_data = {'in_0': ([1], Bits1), 'in_1': ([1], Bits2),
      'in_2[0][0][0]' : ([0], Bits1),
      'in_2[0][0][1]' : ([0], Bits1),
      'in_2[1][0][0]' : ([0], Bits1),
      'in_2[1][0][1]' : ([0], Bits1),
      'in_3' : ( [1], Bits1 ),
      'in_4' : ( [1], Bits1 )
  }

  m._outport_types = {'out0': Bits2, 
      'out1[0][0]' : Bits2,
      'out1[0][1]' : Bits2,
      'out1[1][0]' : Bits2,
      'out1[1][1]' : Bits2,
      'out1[2][0]' : Bits2,
      'out1[2][1]' : Bits2,
      'out2' : Bits1, 'out3' : Bits1
  }

  do_test( m )

def test_port_connection2( do_test ):

  class TestComponent( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      s.connect( s.out, s.in_ )

  m = TestComponent()

  m._input_data = { 'in_': ([1, 0], Bits16) }

  m._outport_types = {'out': Bits16}

  do_test( m )

def test_port_connection3( do_test ):

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits1 )
      s.in_1 = InVPort( Bits1 )
      s.out0 = OutVPort( Bits1 )

      # Output bitwidth = 1

      s.connect( s.in_0, s.out0[0:1] )

  m = TestComponent()

  m._input_data = {'in_0': ([1, 0], Bits1), 'in_1': ([1, 1], Bits1)}

  m._outport_types = {'out0': Bits1}

  do_test( m )

def test_port_connection4( do_test ):

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits2 )
      s.in_1 = InVPort( Bits2 )
      s.in_2 = [ InVPort( Bits2 ) for _ in xrange(2) ]
      s.in_3 = [ InVPort( Bits2 ) for _ in xrange(2) ]
      s.in_4 = InVPort( Bits2 )
      s.out0 = OutVPort( Bits1 )
      s.out1 = OutVPort( Bits2 )
      s.out2 = [ [ OutVPort( Bits2 ) for _ in xrange(2) ] for _ in xrange(3) ]
      s.out3 = OutVPort( Bits2 )

      # Output bitwidth = 17

      s.connect( s.in_0[1:2], s.out0[0:1] )
      s.connect( s.in_0, s.out1[0:2] )
      s.connect( s.in_0, s.out2[0][0][0:2] )
      s.connect( s.in_0, s.out2[0][1][0:2] )
      s.connect( s.in_1, s.out2[1][0][0:2] )
      s.connect( s.in_1, s.out2[1][1][0:2] )
      s.connect( s.in_1[0], s.out2[2][0][0:1] )
      s.connect( s.in_1[0:1], s.out2[2][0][1:2] )
      s.connect( s.in_1[1:2], s.out2[2][1][0:1] )
      s.connect( s.in_2[0][0:1], s.out2[2][1][1:2] )
      s.connect( s.in_2[0][1:2], s.out3[0:1] )
      s.connect( s.in_2[0][0:1], s.out3[1:2] )

  m = TestComponent()

  m._input_data = {'in_0': ([1, 0], Bits2),
    'in_1': ([1, 1], Bits2),
    'in_2[0]': ([1, 1], Bits2),
    'in_2[1]': ([1, 1], Bits2),
    'in_3[0]': ([1, 1], Bits2),
    'in_3[1]': ([1, 1], Bits2),
    'in_4': ([1, 1], Bits2)}

  m._outport_types = {'out0': Bits1,
    'out1': Bits2,
    'out2[0][0]': Bits2,
    'out2[0][1]': Bits2,
    'out2[1][0]': Bits2,
    'out2[1][1]': Bits2,
    'out2[2][0]': Bits2,
    'out2[2][1]': Bits2,
    'out3': Bits2}

  do_test( m )

def test_port_connection5( do_test ):

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits1 )
      s.in_1 = InVPort( Bits2 )
      s.out0 = [ [ [ OutVPort( Bits1 ) for _ in xrange(2) ] for _ in xrange(1) ] for _ in xrange(2) ]
      s.out1 = OutVPort( Bits1 )

      # Output bitwidth = 5
      
      s.connect( s.in_0, s.out0[0][0][0][0:1] )
      s.connect( s.in_0, s.out0[0][0][1][0:1] )
      s.connect( s.in_0, s.out0[1][0][0][0:1] )
      s.connect( s.in_0, s.out0[1][0][1][0:1] )
      s.connect( s.in_1[0:1], s.out1[0:1] )

  m = TestComponent()

  m._input_data = {'in_0': ([0, 1], Bits1), 'in_1':([1,0], Bits2)}

  m._outport_types = {'out1': Bits1,
      'out0[0][0][0]': Bits1,
      'out0[0][0][1]': Bits1,
      'out0[1][0][0]': Bits1,
      'out0[1][0][1]': Bits1,
  }

  do_test( m )

def test_port_connection6( do_test ):
  # Verilator does not allow bit indexing/slicing on a single bit
  # Extra bit slicings will be eliminated by translation framework

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits1 )
      s.in_1 = InVPort( Bits2 )
      s.out0 = [ [ [ OutVPort( Bits1 ) for _ in xrange(2) ] for _ in xrange(1) ] for _ in xrange(2) ]
      s.out1 = OutVPort( Bits1 )

      # Output bitwidth = 5

      s.connect( s.in_0, s.out0[0][0][0][0:1] )
      s.connect( s.in_0[0:1][0:1][0:1][0:1][0:1], s.out0[0][0][1][0:1] )
      s.connect( s.in_0, s.out0[1][0][0][0:1] )
      s.connect( s.in_0, s.out0[1][0][1][0:1] )
      s.connect( s.in_1[0:1], s.out1[0:1] )

  m = TestComponent()

  m._input_data = {'in_0': ([0, 1], Bits1), 'in_1':([1,0], Bits2)}

  m._outport_types = {'out1': Bits1,
      'out0[0][0][0]': Bits1,
      'out0[0][0][1]': Bits1,
      'out0[1][0][0]': Bits1,
      'out0[1][0][1]': Bits1,
  }

  do_test( m )

def test_port_connection7( do_test ):
  # Verilator does not allow bit indexing/slicing on a single bit
  # Extra bit slicings will be eliminated by translation framework

  class TestComponent( RTLComponent ):
    
    def construct( s ):

      s.in_0 = InVPort( Bits95 )
      s.in_1 = InVPort( Bits36 )
      s.in_2 = [ InVPort( Bits14 ) for _ in xrange(9) ]
      s.in_3 = InVPort( Bits42 )
      s.in_4 = InVPort( Bits79 )
      s.out0 = OutVPort( Bits48 )
      s.out1 = [ OutVPort( Bits109 ) for _ in xrange(7) ]
      s.out2 = [ [ [ [ OutVPort( Bits86 ) for _ in xrange(6) ] for _ in xrange(3) ] for _ in xrange(1) ] for _ in xrange(1) ]

      # Output bitwidth = 51043

      s.connect( s.in_0[0:48], s.out0[0:48] )
      s.connect( s.in_0[48:95], s.out1[0][0:47] )
      s.connect( s.in_0[0:62], s.out1[0][47:109] )
      s.connect( s.in_0[62:95], s.out1[1][0:33] )
      s.connect( s.in_0[39], s.out1[1][33:34] )
      s.connect( s.in_0[94], s.out1[1][34:35] )
      s.connect( s.in_1, s.out1[1][35:71] )
      s.connect( s.in_1[5:13][7], s.out1[1][71:72] )
      s.connect( s.in_1[32], s.out1[1][72:73] )
      s.connect( s.in_1[19][0], s.out1[1][73:74] )
      s.connect( s.in_2[3][11:13], s.out1[1][74:76] )
      s.connect( s.in_2[6][10:11], s.out1[1][76:77] )
      s.connect( s.in_2[2][10], s.out1[1][77:78] )
      s.connect( s.in_2[0][8:10][1][0:1][0][0:1][0][0:1], s.out1[1][78:79] )
      s.connect( s.in_3[26:37], s.out1[1][79:90] )
      s.connect( s.in_3[39:40], s.out1[1][90:91] )
      s.connect( s.in_3[0:18], s.out1[1][91:109] )
      s.connect( s.in_3[18:42], s.out1[2][0:24] )
      s.connect( s.in_3, s.out1[2][24:66] )
      s.connect( s.in_4[0:43], s.out1[2][66:109] )
      s.connect( s.in_4[43:79], s.out1[3][0:36] )
      s.connect( s.in_4[71:79][2:7][3:5][0:1][0][0][0:1], s.out1[3][36:37] )
      s.connect( s.in_4[0:72], s.out1[3][37:109] )
      s.connect( s.in_4[72:79], s.out1[4][0:7] )
      s.connect( s.in_4, s.out1[4][7:86] )
      s.connect( s.in_0[0:23], s.out1[4][86:109] )
      s.connect( s.in_0[23:95], s.out1[5][0:72] )
      s.connect( s.in_0[0:37], s.out1[5][72:109] )
      s.connect( s.in_0[37:95], s.out1[6][0:58] )
      s.connect( s.in_0[0:51], s.out1[6][58:109] )
      s.connect( s.in_0[51:95], s.out2[0][0][0][0][0:44] )
      s.connect( s.in_0[0:42], s.out2[0][0][0][0][44:86] )
      s.connect( s.in_0[42:95], s.out2[0][0][0][1][0:53] )
      s.connect( s.in_0[0:33], s.out2[0][0][0][1][53:86] )
      s.connect( s.in_0[33:95], s.out2[0][0][0][2][0:62] )
      s.connect( s.in_0[0:24], s.out2[0][0][0][2][62:86] )
      s.connect( s.in_0[24:95], s.out2[0][0][0][3][0:71] )
      s.connect( s.in_0[0:15], s.out2[0][0][0][3][71:86] )
      s.connect( s.in_0[15:95], s.out2[0][0][0][4][0:80] )
      s.connect( s.in_0[0:6], s.out2[0][0][0][4][80:86] )
      s.connect( s.in_0[6:92], s.out2[0][0][0][5][0:86] )
      s.connect( s.in_0[92:95], s.out2[0][0][1][0][0:3] )
      s.connect( s.in_0[0:83], s.out2[0][0][1][0][3:86] )
      s.connect( s.in_0[83:95], s.out2[0][0][1][1][0:12] )
      s.connect( s.in_0[0:74], s.out2[0][0][1][1][12:86] )
      s.connect( s.in_0[74:95], s.out2[0][0][1][2][0:21] )
      s.connect( s.in_0[0:65], s.out2[0][0][1][2][21:86] )
      s.connect( s.in_0[65:95], s.out2[0][0][1][3][0:30] )
      s.connect( s.in_0[0:56], s.out2[0][0][1][3][30:86] )
      s.connect( s.in_0[56:95], s.out2[0][0][1][4][0:39] )
      s.connect( s.in_0[0:47], s.out2[0][0][1][4][39:86] )
      s.connect( s.in_0[47:95], s.out2[0][0][1][5][0:48] )
      s.connect( s.in_0[0:38], s.out2[0][0][1][5][48:86] )
      s.connect( s.in_0[38:95], s.out2[0][0][2][0][0:57] )
      s.connect( s.in_0[0:29], s.out2[0][0][2][0][57:86] )
      s.connect( s.in_0[29:95], s.out2[0][0][2][1][0:66] )
      s.connect( s.in_0[0:20], s.out2[0][0][2][1][66:86] )
      s.connect( s.in_0[20:95], s.out2[0][0][2][2][0:75] )
      s.connect( s.in_0[0:11], s.out2[0][0][2][2][75:86] )
      s.connect( s.in_0[11:95], s.out2[0][0][2][3][0:84] )
      s.connect( s.in_0[0:2], s.out2[0][0][2][3][84:86] )
      s.connect( s.in_0[2:88], s.out2[0][0][2][4][0:86] )
      s.connect( s.in_0[88:95], s.out2[0][0][2][5][0:7] )
      s.connect( s.in_0[0:79], s.out2[0][0][2][5][7:86] )

  m = TestComponent()

  m._input_data = {
      'in_0': ([21914882267441428730234304116L], Bits95),
      'in_1':([67876138429], Bits36),
      'in_2[0]': ([3841], Bits14),
      'in_2[1]': ([8207], Bits14),
      'in_2[2]': ([14526], Bits14),
      'in_2[3]': ([10113], Bits14),
      'in_2[4]': ([11069], Bits14),
      'in_2[5]': ([4265], Bits14),
      'in_2[6]': ([2979], Bits14),
      'in_2[7]': ([13591], Bits14),
      'in_2[8]': ([8262], Bits14),
      'in_3': ([2284030701503], Bits42),
      'in_4': ([118305075065904913999730L], Bits79)
  }

  m._outport_types = {
      'out0': Bits48,
      'out1[0]': Bits109,
      'out1[1]': Bits109,
      'out1[2]': Bits109,
      'out1[3]': Bits109,
      'out1[4]': Bits109,
      'out1[5]': Bits109,
      'out1[6]': Bits109,
      'out2[0][0][0][0]': Bits86,
      'out2[0][0][0][1]': Bits86,
      'out2[0][0][0][2]': Bits86,
      'out2[0][0][0][3]': Bits86,
      'out2[0][0][0][4]': Bits86,
      'out2[0][0][0][5]': Bits86,
      'out2[0][0][1][0]': Bits86,
      'out2[0][0][1][1]': Bits86,
      'out2[0][0][1][2]': Bits86,
      'out2[0][0][1][3]': Bits86,
      'out2[0][0][1][4]': Bits86,
      'out2[0][0][1][5]': Bits86,
      'out2[0][0][2][0]': Bits86,
      'out2[0][0][2][1]': Bits86,
      'out2[0][0][2][2]': Bits86,
      'out2[0][0][2][3]': Bits86,
      'out2[0][0][2][4]': Bits86,
      'out2[0][0][2][5]': Bits86
  }

  do_test( m )
