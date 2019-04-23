#=========================================================================
# s4_b0_test.py
#=========================================================================
# Tests with value/struct ports/interfaces and connections/subcomponents,
# no upblks.

import pytest, copy

from pymtl import *
from pymtl.passes.utility.test_utility import *
from pymtl.passes.sverilog.import_.helpers import pymtl_name

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

      else: value[0][idx] = Type( *data )

  # Generate reference output

  output_val = gen_sim_reference( m, m._input_data, m._outport_types )

  # Generate translation pass with the given structural & behavioral levels

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTranslator, 4, 0
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

def test_port_connection1( do_test ):

  class ReqType( object ):

    def __init__( s, data=0, len_=0, opaque=0, addr=0 ):

      s.data = Bits40( data )
      s.len_ = Bits4( len_ )
      s.opaque = Bits8( opaque )
      s.addr = Bits16( addr )

    def __eq__( s, o ):

      if type( s ) != type( o ): return False

      return (s.data==o.data) and (s.len_==o.len_) and (s.opaque==o.opaque)\
          and (s.addr==o.addr)

  class TestComponent( Component ):

    def construct( s ):

      s.in_ = InPort( ReqType )
      s.out = OutPort( ReqType )

      s.connect( s.in_, s.out )

  m = TestComponent()

  m._input_data = { 'in_': ( [
    ReqType( 1, 2, 3, 4 ), ReqType( 5, 6, 7, 8 )
  ], ReqType ) }

  m._outport_types = { 'out': ReqType }

  do_test( m )
