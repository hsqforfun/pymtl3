from pymtl import *

# N-input Mux

class Mux(MethodComponent):

  def __init__( s, num_inputs = 2 ):
    s.in_ = [0] * num_inputs
    s.sel = 0
    s.out = 0

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):
    return "[%4d > %4d]" % (s.v1, s.v2)
