#=========================================================================
# BehavioralTrans.py
#=========================================================================
# The complete behavioral translator that inherits from all base
# behavioral translators.
#
# Author : Peitian Pan
# Date   : March 19, 2019

from BaseBehavioralTrans       import DummyBehavioralTrans
from BehavioralUpblkTrans      import BehavioralUpblkTrans
from BehavioralConstraintTrans import BehavioralConstraintTrans

def mk_BehavioralTrans( upblk_trans_level, constraint_trans_level ):
  """
     Construct a BehavioralTrans from the two given levels. This
     allows incremental development and testing.
  """

  assert (0 <= upblk_trans_level <= 1) and (0 <= constraint_trans_level <= 1)

  _BehavioralUpblkTrans = DummyBehavioralTrans if upblk_trans_level==0\
                     else BehavioralUpblkTrans

  _BehavioralConstraintTrans = DummyBehavioralTrans if constraint_trans_level==0\
                     else BehavioralConstraintTrans

  class _BehavioralTrans( _BehavioralUpblkTrans, _BehavioralConstraintTrans ):

    def __init__( s, top ):

      super( _BehavioralTrans, s ).__init__( top )

    def translate( s ):

      super( _BehavioralTrans, s ).translate()

  return _BehavioralTrans

BehavioralTrans =\
    mk_BehavioralTrans( upblk_trans_level = 1, constraint_trans_level = 1 )
