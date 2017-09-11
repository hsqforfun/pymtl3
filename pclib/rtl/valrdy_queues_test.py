import random
from pymtl import *
from valrdy_queues import *
from pclib.ifcs import InValRdyIfc, OutValRdyIfc

class TestVectorSimulator( object ):

  def __init__( self, model, test_vectors,
                set_inputs_func, verify_outputs_func, wait_cycles = 0 ):

    self.model               = model
    self.set_inputs_func     = set_inputs_func
    self.verify_outputs_func = verify_outputs_func
    self.test_vectors        = test_vectors
    self.wait_cycles         = wait_cycles

  def run_test( self ):

    SimLevel3Pass().apply( self.model )

    print()
    for test_vector in self.test_vectors:

      # Set inputs
      self.set_inputs_func( self.model, test_vector )
      self.model.tick()

      # Print the line trace
      print self.model.line_trace()

      # Verify outputs
      self.verify_outputs_func( self.model, test_vector )

def run_test_queue( model, test_vectors ):

  # Define functions mapping the test vector to ports in model

  def tv_in( model, tv ):
    model.enq.val = tv[0]
    model.enq.msg = tv[2]
    model.deq.rdy = tv[4]

  def tv_out( model, tv ):
    if tv[1] != '?': assert model.enq.rdy == tv[1]
    if tv[3] != '?': assert model.deq.val == tv[3]
    if tv[5] != '?': assert model.deq.msg == tv[5]

  # Run the test

  sim = TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_bypass_int():

  run_test_queue( BypassQueue1RTL( int ), [
    # enq.val enq.rdy enq.msg deq.val deq.rdy deq.msg
    [    1   ,   1   ,  123  ,   1   ,   1   ,  123  ],
    [    1   ,   1   ,  345  ,   1   ,   0   ,  345  ],
    [    1   ,   0   ,  567  ,   1   ,   0   ,  345  ],
    [    1   ,   0   ,  567  ,   1   ,   1   ,  345  ],
    [    1   ,   1   ,  567  ,   1   ,   1   ,  567  ],
    [    0   ,   1   ,  0    ,   0   ,   1   ,  '?'  ],
    [    0   ,   1   ,  0    ,   0   ,   0   ,  '?'  ],
  ] )

def test_bypass_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( BypassQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(345), B1(1) , B1(0) ,B32(345) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(345) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(1) ,B32(345) ],
    [  B1(1) , B1(1) ,B32(567), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(1) ,  '?'    ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )

def test_pipe_int():

  run_test_queue( PipeQueue1RTL( int ), [
    # enq.val enq.rdy enq.msg deq.val deq.rdy deq.msg
    [    1   ,   1   ,  123  ,   0   ,   1   ,  '?'  ],
    [    1   ,   0   ,  345  ,   1   ,   0   ,  123  ],
    [    1   ,   0   ,  567  ,   1   ,   0   ,  123  ],
    [    1   ,   1   ,  567  ,   1   ,   1   ,  123  ],
    [    1   ,   1   ,  789  ,   1   ,   1   ,  567  ],
    [    0   ,   1   ,  0    ,   1   ,   1   ,  789  ],
    [    0   ,   1   ,  0    ,   0   ,   0   ,  '?'  ],
  ] )

def test_pipe_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( PipeQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(0) , B1(1) ,  '?'    ],
    [  B1(1) , B1(0) ,B32(345), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(567), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(789), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(1) , B1(1) ,B32(789) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )


def test_normal_int():

  run_test_queue( NormalQueue1RTL( int ), [
    # enq.val enq.rdy enq.msg deq.val deq.rdy deq.msg
    [    1   ,   1   ,  123  ,   0   ,   1   ,  '?'  ],
    [    1   ,   0   ,  345  ,   1   ,   0   ,  123  ],
    [    1   ,   0   ,  567  ,   1   ,   0   ,  123  ],
    [    1   ,   0   ,  567  ,   1   ,   1   ,  123  ],
    [    1   ,   1   ,  567  ,   0   ,   1   ,  123  ],
    [    0   ,   0   ,  0    ,   1   ,   1   ,  567  ],
    [    0   ,   1   ,  0    ,   0   ,   0   ,  '?'  ],
  ] )

def test_normal_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( NormalQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(0) , B1(1) ,  '?'    ],
    [  B1(1) , B1(0) ,B32(345), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(567), B1(0) , B1(1) ,B32(123) ],
    [  B1(0) , B1(0) ,B32(0  ), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )
