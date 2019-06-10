#=========================================================================
# test_stateful_rob_test
#=========================================================================
# Tests for test_stateful using a reorder buffer
#
# Author: Yixiao Zhang
#   Date: May 1, 2019

from __future__ import absolute_import, division, print_function

import math

from pymtl3 import *

from .test_stateful import run_test_state_machine
from .test_wrapper import *


#-------------------------------------------------------------------------
# ReorderBufferCL
#-------------------------------------------------------------------------
class ReorderBufferCL( Component ):

  def construct( s, num_entries ):
    # We want to be a power of two so mod arithmetic is efficient
    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries
    s.num_entries = num_entries

    s.data = [ None ] * s.num_entries
    s.allocated = [ 0 ] * s.num_entries

    s.head = 0
    s.num = 0
    s.next_slot = 0

    s.add_constraints(
        M( s.update_entry ) < M( s.remove ),
        M( s.remove ) < M( s.alloc ) )

  @non_blocking( lambda s: s.num < s.num_entries )
  def alloc( s ):
    index = s.next_slot
    s.allocated[ s.next_slot ] = True
    s.num += 1
    s.next_slot = ( s.next_slot + 1 ) % s.num_entries
    return index

  @non_blocking( lambda s: not s.empty() )
  def update_entry( s, index, value ):
    assert index >= 0 and index < s.num_entries
    if s.allocated[ index ]:
      s.data[ index ] = value

  @non_blocking( lambda s: s.data[ s.head ] != None )
  def remove( s ):
    head = s.head
    data = s.data[ s.head ]
    s.data[ s.head ] = None
    s.allocated[ s.head ] = False
    s.head = ( s.head + 1 ) % s.num_entries
    s.num -= 1
    return data

  def empty( s ):
    return s.num == 0

  def line_trace( s ):
    return ""


#-------------------------------------------------------------------------
# clog2
#-------------------------------------------------------------------------
def clog2( num ):
  return int( math.ceil( math.log( num, 2 ) ) )


#-------------------------------------------------------------------------
# AllocIfcRTL
#-------------------------------------------------------------------------
class AllocIfcRTL( Interface ):

  def construct( s, Type, IndexType ):

    s.index = OutPort( IndexType )
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )


#-------------------------------------------------------------------------
# UpdateIfcRTL
#-------------------------------------------------------------------------
class UpdateIfcRTL( Interface ):

  def construct( s, Type, IndexType ):

    s.value = InPort( Type )
    s.index = InPort( IndexType )
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )


#-------------------------------------------------------------------------
# RemoveIfcRTL
#-------------------------------------------------------------------------
class RemoveIfcRTL( Interface ):

  def construct( s, Type ):

    s.value = OutPort( Type )
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )


#-------------------------------------------------------------------------
# ReorderBuffer
#-------------------------------------------------------------------------
class ReorderBuffer( Component ):
  # This stores (key, value) pairs in a finite size FIFO queue
  def construct( s, DataType, num_entries ):
    # We want to be a power of two so mod arithmetic is efficient
    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries
    # Dealloc from head, add onto tail
    index_type = mk_bits( idx_nbits )
    s.head = Wire( index_type )
    s.tail = Wire( index_type )
    s.num = Wire( mk_bits( idx_nbits + 1 ) )

    s.data = [ Wire( DataType ) for _ in range( num_entries ) ]
    s.valid = [ Wire( Bits1 ) for _ in range( num_entries ) ]
    s.allocated = [ Wire( Bits1 ) for _ in range( num_entries ) ]

    # These are the methods that can be performed
    s.alloc = AllocIfcRTL( DataType, index_type )
    s.update_entry = UpdateIfcRTL( DataType, index_type )
    s.remove = RemoveIfcRTL( DataType )

    s.empty = Wire( Bits1 )

    @s.update
    def update_rdy_update():
      s.empty = s.num == 0
      s.update_entry.rdy = not s.empty

    @s.update
    def update_rdy_remove():
      s.remove.rdy = s.valid[
          s.head ] or s.update_entry.en and s.update_entry.index == s.head

    @s.update
    def update_rdy_alloc():
      s.alloc.rdy = s.num < num_entries or s.remove.en

    @s.update
    def update_ret_alloc():
      s.alloc.index = s.tail

    @s.update
    def update_en():
      if s.update_entry.en and s.update_entry.index == s.head:
        s.remove.value = s.update_entry.value
      else:
        s.remove.value = s.data[ s.head ]

    @s.update_on_edge
    def update_num():
      if s.reset:
        s.num = 0
      elif s.alloc.en and not s.remove.en:
        s.num = s.num + 1
      elif not s.alloc.en and s.remove.en:
        s.num = s.num - 1
      else:
        s.num = s.num

    @s.update_on_edge
    def update_tail():
      if s.reset:
        s.tail = 0
      else:
        s.tail = index_type( s.tail + 1 ) if s.alloc.en else s.tail

    @s.update_on_edge
    def update_head():
      if s.reset:
        s.head = 0
      else:
        s.head = index_type( s.head + 1 ) if s.remove.en else s.head

    @s.update_on_edge
    def handle_data_and_flags():
      if s.reset:
        for i in range( num_entries ):
          s.data[ i ] = 0

      # Handle update
      if s.update_entry.en:
        if s.allocated[ s.update_entry.index ]:
          s.data[ s.update_entry.index ] = s.update_entry.value
          s.valid[ s.update_entry.index ] = 1

      if s.remove.en:
        s.valid[ s.head ] = 0
        s.allocated[ s.head ] = 0

      if s.alloc.en:
        s.allocated[ s.tail ] = 1

  def line_trace( s ):
    return ":".join([
        "{}".format( s.data[ i ] if s.valid[ i ] else "......" if s
                     .allocated[ i ] else "-" ).ljust( 8 )
        for i in range( len( s.data ) )
    ] )


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test = run_test_state_machine(
      RTL2CLWrapper( ReorderBuffer( Bits16, 4 ) ), ReorderBufferCL( 4 ) )