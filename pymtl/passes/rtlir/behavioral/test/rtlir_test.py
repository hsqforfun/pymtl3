#=========================================================================
# rtlir_test.py
#=========================================================================
# This file includes directed test cases for the RTLIR generation pass.
#
# Author : Peitian Pan
# Date   : Feb 2, 2019

import pytest

from pymtl                             import *
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl.passes.utility.test_utility import expected_failure, do_test

from .. import BehavioralRTLIRGenPass
from ..errors                          import PyMTLTypeError

#-------------------------------------------------------------------------
# local_do_test
#-------------------------------------------------------------------------
# Verify that the generated RTLIR is the same as the manually generated
# reference.

def local_do_test( m ):

  ref = m._rtlir_test_ref
  m.elaborate()
  BehavioralRTLIRGenPass()( m )
  BehavioralRTLIRTypeCheckPass()( m )

  for blk in m.get_update_blocks():
    assert\
      m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] == ref[ blk.__name__ ]

#-------------------------------------------------------------------------
# test_index_basic
#-------------------------------------------------------------------------

def test_index_basic( do_test ):
  class index_basic( RTLComponent ):
    def construct( s ):
      s.in_ = [ InVPort( Bits16 ) for _ in xrange( 4 ) ]
      s.out = [ OutVPort( Bits16 ) for _ in xrange( 2 ) ]

      @s.update
      def index_basic():
        s.out[ 0 ] = s.in_[ 0 ] + s.in_[ 1 ]
        s.out[ 1 ] = s.in_[ 2 ] + s.in_[ 3 ]

  a = index_basic()

  a._rtlir_test_ref = { 'index_basic' : CombUpblk( 'index_basic', [
    Assign( Index( Attribute( Base( a ), 'out' ), Number( 0 ) ),
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 0 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ) ) ),
    Assign( Index( Attribute( Base( a ), 'out' ), Number( 1 ) ),
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ) ) )
  ] ) }

  a._test_vector = [
          'in_[0]     in_[1]    in_[2]    in_[3]    *out[0]     *out[1]',
    [     Bits16,    Bits16,   Bits16,   Bits16,    Bits16,     Bits16 ],

    [          0,         1,        2,        3,         1,          5 ],
    [ Bits16(-1),         1, Bits16(-1),      1,         0,          0 ],
    [          9,         8,        7,        6,        17,         13 ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_mismatch_width_assign
#-------------------------------------------------------------------------

def test_mismatch_width_assign( do_test ):
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def mismatch_width_assign():
        s.out = s.in_

  a = A()

  a._rtlir_test_ref = { 'mismatch_width_assign' : CombUpblk(
    'mismatch_width_assign', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute( Base( a ), 'in_' )
    )
  ] ) }

  a._test_vector = [
                'in_             *out',
    [        Bits16,           Bits8 ],

    [             0,               0 ],
    [             2,               2 ],
    [    Bits16(-1),       Bits8(-1) ],
    [    Bits16(-2),       Bits8(-2) ],
    [ Bits16(32767),      Bits8(255) ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_slicing_basic
#-------------------------------------------------------------------------

def test_slicing_basic( do_test ):
  class slicing_basic( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits32 )
      s.out = OutVPort( Bits64 )

      @s.update
      def slicing_basic():
        s.out[ 0:16 ] = s.in_[ 16:32 ]
        s.out[ 16:32 ] = s.in_[ 0:16 ]

  a = slicing_basic()

  a._rtlir_test_ref = { 'slicing_basic' : CombUpblk( 'slicing_basic', [
    Assign( Slice( Attribute( Base( a ), 'out' ), Number( 0 ), Number( 16 ) ),
      Slice( Attribute( Base( a ), 'in_' ), Number( 16 ), Number( 32 ) ) ),
    Assign( Slice( Attribute( Base( a ), 'out' ), Number( 16 ), Number( 32 ) ),
      Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 16 ) ) )
  ] ) }

  a._test_vector = [
                'in_                        *out',
    [        Bits32,                     Bits64 ],

    [             0,                          0 ],
    [             2,            Bits64(0x20000) ],
    [    Bits32(-1),         Bits64(0xffffffff) ],
    [    Bits32(-2),         Bits64(0xfffeffff) ],
    [ Bits32(32767),         Bits64(0x7fff0000) ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_bits_basic
#-------------------------------------------------------------------------

def test_bits_basic( do_test ):
  class bits_basic( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      @s.update
      def bits_basic():
        s.out = s.in_ + Bits16( 10 )

  a = bits_basic()

  a._rtlir_test_ref = { 'bits_basic' : CombUpblk( 'bits_basic', [
    Assign( Attribute( Base( a ), 'out' ),
      BinOp( Attribute( Base( a ), 'in_' ), Add(), BitsCast( 16, Number( 10 ) ) ) )
  ] ) }

  a._test_vector = [
                'in_              *out',
    [        Bits16,           Bits16 ],
    [             0,               10 ],
    [             2,               12 ],
    [    Bits16(-1),        Bits16(9) ],
    [    Bits16(-2),        Bits16(8) ],
    [Bits16(0x7FFF),   Bits16(0x8009) ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_index_bits_slicing
#-------------------------------------------------------------------------

def test_index_bits_slicing( do_test ):
  class index_bits_slicing( RTLComponent ):
    def construct( s ):
      s.in_ = [ InVPort( Bits16 ) for _ in xrange( 10 ) ]
      s.out = [ OutVPort( Bits16 ) for _ in xrange( 5 ) ]

      @s.update
      def index_bits_slicing():
        s.out[0][0:8] = s.in_[1][8:16] + s.in_[2][0:8] + Bits8( 10 )
        s.out[1] = s.in_[3][0:16] + s.in_[4] + Bits16( 1 )

  a = index_bits_slicing()

  a._rtlir_test_ref = { 'index_bits_slicing' : CombUpblk( 'index_bits_slicing', [
    Assign( Slice( 
      Index( Attribute( Base( a ), 'out' ), Number( 0 ) ),
      Number( 0 ), Number( 8 ) 
      ),
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ), Number( 8 ), Number( 16 ) ),
          Add(),
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Number( 0 ), Number( 8 ) ),
        ),
        Add(),
        BitsCast( 8, Number( 10 ) )
      )
    ),
    Assign( 
      Index( Attribute( Base( a ), 'out' ), Number( 1 ) ),
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ), Number( 0 ), Number( 16 ) ),
          Add(),
          Index( Attribute( Base( a ), 'in_' ), Number( 4 ) )
        ),
        Add(),
        BitsCast( 16, Number( 1 ) )
      )
    ),
  ] ) }

  a._test_vector = [
      'in_[0] in_[1] in_[2] in_[3] in_[4] in_[5] in_[6] in_[7] in_[8] in_[9]\
          *out[0] *out[1] *out[2] *out[3] *out[4]',
    [ Bits16 ] * 15,

    # 8-bit truncation!
    [ Bits16(0xff) ] * 10 + [ Bits16(0x09), Bits16(0x01ff), 0, 0, 0 ],
    [ Bits16(0x00) ] * 10 + [ Bits16(0x0a), Bits16(0x0001), 0, 0, 0 ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_multi_components
#-------------------------------------------------------------------------

def test_multi_components( do_test ):
  class multi_components_B( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      @s.update
      def multi_components_B():
        s.out = s.in_

  class multi_components_A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )
      s.b = multi_components_B()

      # There should be a way to check module connections?
      s.connect( s.in_, s.b.in_ )

      @s.update
      def multi_components_A():
        s.out = s.in_ + s.b.out

  a = multi_components_A()

  a._rtlir_test_ref = { 'multi_components_A' : CombUpblk( 'multi_components_A', [
    Assign( Attribute( Base( a ), 'out' ),
      BinOp(
        Attribute( Base( a ), 'in_' ),
        Add(),
        Attribute( Attribute( Base( a ), 'b' ), 'out' )
      ) 
    )
  ] ) }

  a._test_vector = [
                'in_              *out',
    [ Bits16 ] *2,

    [             0,               0 ],
    [             2,               4 ],
    [    Bits16(-1),      Bits16(-2) ],
    [    Bits16(-2),      Bits16(-4) ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_if_basic
#-------------------------------------------------------------------------

def test_if_basic( do_test ):
  class if_basic( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def if_basic():
        if s.in_[ 0:8 ] == Bits8( 255 ):
          s.out = s.in_[ 8:16 ]
        else:
          s.out = Bits8( 0 )

  a = if_basic()

  a._rtlir_test_ref = {
    'if_basic' : CombUpblk( 'if_basic', [ If(
      Compare( Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 8 ) ), Eq(), BitsCast( 8, Number( 255 ) ) ),
      [ Assign( Attribute( Base( a ), 'out' ), Slice( Attribute( Base( a ), 'in_' ), Number( 8 ), Number( 16 ) ) ) ],
      [ Assign( Attribute( Base( a ), 'out' ), BitsCast( 8, Number( 0 ) ) ) ]
    )
  ] ) }

  a._test_vector = [
                'in_              *out',
    [         Bits16,           Bits8 ],
    [           255,                0 ],
    [           511,                1 ],
    [           256,                0 ],
  ]

  do_test( a )

#-------------------------------------------------------------------------
# test_for_basic
#-------------------------------------------------------------------------

def test_for_basic( do_test ):
  class for_basic( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def for_basic():
        for i in xrange( 8 ):
          s.out[ 2*i:2*i+1 ] = s.in_[ 2*i:2*i+1 ] + s.in_[ 2*i+1:2*i+2 ]

  a = for_basic()

  twice_i = BinOp( Number( 2 ), Mult(), LoopVar( 'i' ) )

  a._rtlir_test_ref = {
    'for_basic' : CombUpblk( 'for_basic', [ For(
      LoopVarDecl( 'i' ), Number( 0 ), Number( 8 ), Number( 1 ),
      [ Assign(
          Slice( Attribute( Base( a ), 'out' ), twice_i, BinOp( twice_i, Add(), Number( 1 ) ) ),
          BinOp(
            Slice( Attribute( Base( a ), 'in_' ), twice_i, BinOp( twice_i, Add(), Number( 1 ) ) ),
            Add(),
            Slice( Attribute( Base( a ), 'in_' ),
              BinOp( twice_i, Add(), Number( 1 ) ),
              BinOp( twice_i, Add(), Number( 2 ) )
            )
          )
      ) 
    ]
    ) ] )
  }

  a._test_vector = []

  do_test( a )

#-------------------------------------------------------------------------
# test_multi_upblks
#-------------------------------------------------------------------------

def test_multi_upblks( do_test ):
  class multi_upblks( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits4 )
      s.out = OutVPort( Bits8 )

      @s.update
      def multi_upblks_1():
        s.out[ 0:4 ] = s.in_

      @s.update
      def multi_upblks_2():
        s.out[ 4:8 ] = s.in_

  a = multi_upblks()

  a._rtlir_test_ref = { 'multi_upblks_1' : CombUpblk( 'multi_upblks_1', [
      Assign( Slice( Attribute( Base( a ), 'out' ), Number(0), Number(4) ), Attribute( Base( a ), 'in_' ) ),
    ] ),
    'multi_upblks_2' : CombUpblk( 'multi_upblks_2', [
      Assign( Slice( Attribute( Base( a ), 'out' ), Number(4), Number(8) ), Attribute( Base( a ), 'in_' ) ),
    ] )
  }

  a._test_vector = [
                'in_              *out',
    [         Bits4,            Bits8 ],

    [     Bits4(-1),      Bits8(0xff) ],
    [      Bits4(1),      Bits8(0x11) ],
    [      Bits4(7),      Bits8(0x77) ],
  ]

  do_test( a )
