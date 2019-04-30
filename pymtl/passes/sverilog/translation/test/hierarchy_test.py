#=========================================================================
# hierarchy_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL hierarchical designs.
# 
# Author : Shunning Jiang, Peitian Pan
# Date   : Feb 21, 2019

from pymtl                             import *
from pymtl.passes.utility.test_utility import expected_failure
from pymtl.dsl.errors                  import SignalTypeError

def test_deep_connection():
  class Deep( Component ):
    def construct( s ):
      s.out = OutPort( Bits1 )
      s.deep = Wire( Bits1 )

      @s.update
      def out_blk():
        s.out = s.deep

  class Bar( Component ):
    def construct( s ):
      s.deep = Deep()

  class Foo( Component ):
    def construct( s ):
      s.bar = Bar()
      s.foo = InPort( Bits1 )
      s.connect( s.foo, s.bar.deep.deep )

  with expected_failure( SignalTypeError ):
    foo = Foo()
    foo.elaborate() # Should fail because the connection is too deep
