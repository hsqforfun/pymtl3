"""
========================================================================
ComponentAPI_test.py
========================================================================

Author : Shunning Jiang
Date   : June 2, 2019
"""
import random

from pymtl3.datatypes import *
from pymtl3.dsl import Component, InPort, OutPort, Placeholder, Wire, connect
from pymtl3.dsl.errors import InvalidAPICallError

from .sim_utils import simple_sim_pass


def test_api_not_elaborated():

  class X( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      @s.update
      def up_x():
        s.out = s.in_ + 1

  class Y( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.x = X()( in_ = s.in_, out = s.out )

  a = Y()
  a.elaborate()
  try:
    a.x.get_all_update_blocks()
  except InvalidAPICallError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidAPICallError.")

# The following two tests cases test x.replace_component()

class Foo_shamt( Placeholder, Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )

    # Nothing here

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real_shamt( Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )
    @s.update
    def up_real():
      s.out = s.in_ << shamt

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Real_shamt2( Component ):
  def construct( s, shamt=1 ):
    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits32 )
    @s.update
    def up_real():
      s.out = s.in_ + shamt

  def line_trace( s ):
    return "{}>{}".format( s.in_, s.out )

class Foo_shamt_list_wrap( Component ):
  def construct( s, nbits=0 ):
    s.in_ = InPort ( mk_bits(nbits) )
    s.out = [ OutPort( mk_bits(nbits) ) for i in range(5) ]

    s.inner = [ Foo_shamt( i )( in_ = s.in_, out = s.out[i] ) for i in range(5) ]

  def line_trace( s ):
    return "|".join( [ x.line_trace() for x in s.inner ] )

def test_real_replaced_by_real2():

  class Real_wrap( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.w   = Wire( mk_bits(nbits) )
      connect( s.w, s.out )

      s.inner = Real_shamt( 5 )( in_ = s.in_, out = s.w )

    def line_trace( s ):
      return s.inner.line_trace()

  foo_wrap = Real_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real_shamt2, check=True )

  simple_sim_pass( foo_wrap )
  foo_wrap.sim_reset()

  foo_wrap.in_ = Bits32(100)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 105

  foo_wrap.in_ = Bits32(3)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 8

def test_replace_component_list_of_foo_by_real():

  foo_wrap = Foo_shamt_list_wrap( 32 )

  foo_wrap.elaborate()
  order = list(range(5))
  random.shuffle( order )
  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt )

  simple_sim_pass( foo_wrap )

  print()
  foo_wrap.in_ = Bits32(16)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

  foo_wrap.in_ = Bits32(4)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

def test_replace_component_list_of_real_by_real2():

  foo_wrap = Foo_shamt_list_wrap( 32 )

  order = list(range(5))
  random.shuffle( order )

  foo_wrap.elaborate()

  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt )

  random.shuffle( order )
  for i in order:
    foo_wrap.replace_component( foo_wrap.inner[i], Real_shamt2 )

  print(len(foo_wrap._dsl.connect_order))
  simple_sim_pass( foo_wrap )

  print()
  foo_wrap.in_ = Bits32(16)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

  foo_wrap.in_ = Bits32(4)
  foo_wrap.tick()
  print(foo_wrap.line_trace())

# This test is to test if we save the fact that up_in writes the inport
# of the inner module and recover it when we put in the new component

def test_replace_component_upblk_rw_port():

  class Real_wrap( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.w   = Wire( mk_bits(nbits) )
      connect( s.w, s.out )

      @s.update
      def up_in():
        s.inner.in_ = s.in_

      @s.update
      def up_out():
        s.w = s.inner.out

      s.inner = Real_shamt( 5 )#( in_ = s.in_, out = s.w )

    def line_trace( s ):
      return s.inner.line_trace()

  foo_wrap = Real_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real_shamt2, check=True )

  simple_sim_pass( foo_wrap )
  foo_wrap.sim_reset()

  foo_wrap.in_ = Bits32(100)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 105

  foo_wrap.in_ = Bits32(3)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 8


# This test is the extended version of the previous one which tests if we
# save and recover functions in the parent correctly

def test_replace_component_func_rw_port():

  class Real_wrap( Component ):
    def construct( s, nbits=0 ):
      s.in_ = InPort ( mk_bits(nbits) )
      s.out = OutPort( mk_bits(nbits) )
      s.w   = Wire( mk_bits(nbits) )
      connect( s.w, s.out )

      @s.func
      def assign_in( x ):
        s.inner.in_ = x

      @s.update
      def up_in():
        assign_in( s.in_ )

      @s.func
      def read_out():
        s.w = s.inner.out

      @s.update
      def up_out():
        read_out()

      s.inner = Real_shamt( 5 )#( in_ = s.in_, out = s.w )

    def line_trace( s ):
      return s.inner.line_trace()

  foo_wrap = Real_wrap( 32 )

  foo_wrap.elaborate()
  foo_wrap.replace_component( foo_wrap.inner, Real_shamt2, check=True )

  simple_sim_pass( foo_wrap )
  foo_wrap.sim_reset()

  foo_wrap.in_ = Bits32(100)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 105

  foo_wrap.in_ = Bits32(3)
  foo_wrap.tick()
  print(foo_wrap.line_trace())
  assert foo_wrap.out == 8

def test_ctrl_dpath_connected_replaced_both():

  class Module1( Component ):
    def construct( s ):
      s.in_  = InPort( Bits32 )
      s.wire = Wire( Bits32 )
      s.out  = OutPort( Bits32 )

      connect( s.in_, s.wire )

      @s.update
      def out():
        s.out = s.wire + 10

  class Module2( Component ):
    def construct( s ):
      s.in_  = InPort( Bits32 )
      s.wire = Wire( Bits32 )
      s.out  = OutPort( Bits32 )

      connect( s.in_, s.wire )

      @s.update
      def out():
        s.out = s.wire + 444

  class Inner( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.m1  = Module1()
      s.m2  = Module1()
      s.out = OutPort( Bits32 )

      connect( s.in_, s.m1.in_ )
      connect( s.m1.out, s.m2.in_ )
      connect( s.m2.out, s.out )

  class Top( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.inner = Inner()
      s.out = OutPort( Bits32 )

      connect( s.in_, s.inner.in_)
      connect( s.inner.out, s.out )

    def line_trace( s ):
      return "{} > {}".format( s.in_, s.out )

  a = Top()

  a.elaborate()
  a.replace_component( a.inner.m1, Module2() )
  a.replace_component( a.inner.m2, Module2() )

  simple_sim_pass( a )

  a.in_ = Bits32(10)
  a.tick()
  assert a.out == 10 + 444 * 2

# def test_garbage_collection():

  # class X( Component ):
    # def construct( s, nbits=0 ):
      # s.leak = bytearray(1<<30)
      # s.in_ = InPort ( mk_bits(nbits) )
      # s.out = OutPort( mk_bits(nbits) )
      # @s.update
      # def up_x():
        # s.out = s.in_ + 1
  # for i in range(100):
    # x = X()
    # x = X()
