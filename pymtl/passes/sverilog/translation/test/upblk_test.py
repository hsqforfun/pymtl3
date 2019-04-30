#=========================================================================
# upblk_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL models with complicated expressions insdie
# one upblk.
# 
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from pymtl.passes.rtlir.behavioral.test.rtlir_test import *
from pymtl.passes.sverilog              import TranslationPass, SimpleImportPass
from pymtl.passes.rtlir.test_utility import do_test
from pymtl.passes.sverilog.test_utility  import run_translation_reference_test

def local_do_test( m ):

  def run_sv_translation_test( m, test_vector ):
    # Convert input data to desired type
    for num_case, test_case in enumerate(test_vector[2:]):
      for idx, element in enumerate(test_case):
        if element == '*': continue
        if not isinstance( element, test_vector[1][idx] ):
          test_vector[num_case+2][idx] = test_vector[1][idx]( element )

    run_translation_reference_test(
      m, test_vector, TranslationPass, SimpleImportPass
    )

  run_sv_translation_test( m, m._test_vector )

# Reuse tests from passes/rast/test/rast_test.py
[ pytest.mark.skip(x) for x in [
  test_for_basic, test_mismatch_width_assign
] ]

#-------------------------------------------------------------------------
# test_struct_inport
#-------------------------------------------------------------------------
# The original test case invovles parameterized struct types. We have not
# found a clean way to do that yet...

def test_struct_inport( do_test ):
  class struct_fields( object ):
    def __init__( s, foo = 0, bar = 0 ):
      s.foo = Bits4( foo )
      s.bar = Bits8( bar )

      s._pack_order = [ 'foo', 'bar' ]

    def __call__( s, foo = 0, bar = 0 ):
      msg = struct_fields( s.foo.nbits, s.bar.nbits )
      msg.foo = msg.foo( foo )
      msg.bar = msg.bar( bar )
      return msg

  class struct_inport( Component ):
    def construct( s, n_foo, n_bar ):
      s.in_ = InPort( struct_fields )
      s.out = OutPort( mk_bits( n_foo + n_bar ) )

      @s.update
      def struct_inport():
        s.out[ 0:n_foo ] = s.in_.foo
        s.out[ n_foo:n_foo+n_bar ] = s.in_.bar

  a = struct_inport( 4, 8 )
  a._test_vector = [
                    'in_             *out',
    [     struct_fields,          Bits12 ],
    [ struct_fields( 0xF, 0x00 ), Bits12( 0x00F ) ],
    [ struct_fields( 0x0, 0xF0 ), Bits12( 0xF00 ) ],
    [ struct_fields( 0x0, 0x0F ), Bits12( 0x0F0 ) ],
    [ struct_fields( 0xB, 0xCA ), Bits12( 0xCAB ) ],
    [ struct_fields( 0xA, 0xDF ), Bits12( 0xDFA ) ],
    [ struct_fields( 0x0, 0x01 ), Bits12( 0x010 ) ],

    # [   Bits12( 0xF00 ), Bits12( 0x00F ) ],
    # [   Bits12( 0x0F0 ), Bits12( 0xF00 ) ],
    # [   Bits12( 0x00F ), Bits12( 0x0F0 ) ],
    # [   Bits12( 0xBCA ), Bits12( 0xCAB ) ],
    # [   Bits12( 0xADF ), Bits12( 0xDFA ) ],
    # [   Bits12( 0x001 ), Bits12( 0x010 ) ],
    # [   Bits12( 0x702 ), Bits12( 0x027 ) ],
    # [   Bits12( 0xF05 ), Bits12( 0x05F ) ],
    # [   Bits12( 0x0FC ), Bits12( 0xFC0 ) ],
  ]
  do_test( a )

#-------------------------------------------------------------------------
# test_composite_port
#-------------------------------------------------------------------------

def test_composite_port( do_test ):
  class val_bundle( object ):
    def __init__( s, val0 = 0, val1 = 0 ):
      s.val0 = Bits1( val0 )
      s.val1 = Bits1( val1 )
      
      s._pack_order = [ 'val0', 'val1' ]

  class composite_port( Component ):
    def construct( s, num_port ):
      s.in_ = [ InPort( val_bundle ) for _ in xrange( num_port ) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange( num_port ) ]

      @s.update
      def composite_port_out():
        for i in xrange( num_port ):
          if s.in_[ i ].val0 and s.in_[ i ].val1:
            s.out[ i ] = Bits32(0xac)
          else:
            s.out[ i ] = Bits32(0xff)

  m = composite_port( 2 )
  m._test_vector = [
    '    in_[0]    in_[1]       *out[0]      *out[1] ',
    [val_bundle,val_bundle,       Bits32,       Bits32 ],

    [val_bundle(1, 1), val_bundle(1, 1), Bits32(0xac), Bits32(0xac)],
    [val_bundle(0, 1), val_bundle(0, 1), Bits32(0xff), Bits32(0xff)],
    [val_bundle(1, 1), val_bundle(0, 1), Bits32(0xac), Bits32(0xff)],
    [val_bundle(0, 1), val_bundle(1, 1), Bits32(0xff), Bits32(0xac)],

    # [ Bits2(3), Bits2(3), Bits32(0xac), Bits32(0xac) ],
    # [ Bits2(1), Bits2(1), Bits32(0xff), Bits32(0xff) ],
    # [ Bits2(3), Bits2(1), Bits32(0xac), Bits32(0xff) ],
    # [ Bits2(1), Bits2(3), Bits32(0xff), Bits32(0xac) ],
  ]
  do_test( m )
