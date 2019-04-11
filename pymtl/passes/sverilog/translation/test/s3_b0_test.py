#=========================================================================
# s3_b0_test.py
#=========================================================================
# Tests with value/struct ports/interfaces and connections, no upblks.

import pytest, copy

from pymtl import *
from pymtl.passes.utility import is_BitsX
from pymtl.passes.utility.test_utility import *
from pymtl.passes.sverilog.import_.helpers import pymtl_name
from pclib.ifcs.ValRdyIfc import InValRdyIfc, OutValRdyIfc

from ..SVRTLIRTranslator import mk_SVRTLIRTranslator
from ..TranslationPass   import mk_TranslationPass
from ....                import SimpleImportPass

from pclib.ifcs.MemMsg import *

def local_do_test( m ):

  m_copy = copy.deepcopy( m )

  # Convert the input data into correct type

  for key, value in m._input_data.iteritems():
    Type = value[1]

    for idx, data in enumerate( value[0] ):

      if isinstance( data, Type ): continue

      elif is_BitsX( Type ): value[0][idx] = Type( data )

      else: value[0][idx] = Type( *data )

  # Generate reference output

  output_val = gen_sim_reference( m, m._input_data, m._outport_types )

  # Generate translation pass with the given structural & behavioral levels

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTranslator, 3, 0
  )

  # Verfiy the imported model against the reference output

  run_sim_reference_test(
    m_copy, m._input_data, m._outport_types, output_val,
    translation_pass, SimpleImportPass
  )

  # Calling `finalize()` is necessary to immediately destroy the cached
  # dynamic library in CFFI

  m_copy._pass_simple_import.imported_model.finalize()
  del m_copy
  del m

def test_ifc_connection1( do_test ):

  class TestComponent( Component ):

    def construct( s ):

      s.in_ = InValRdyIfc( Bits16 )
      s.out = OutValRdyIfc( Bits16 )

      s.connect( s.in_, s.out )

  m = TestComponent()

  m._input_data = {
    'in_.msg' : ( [ 233, 123, 321 ], Bits16 ),
    'in_.val' : ( [   1,   0,   1 ], Bits1 ),
    'out.rdy' : ( [   1,   1,   0 ], Bits1 )
  }

  m._outport_types = {
    'in_.rdy' : Bits1,
    'out.msg' : Bits16,
    'out.val' : Bits1
  }

  do_test( m )
