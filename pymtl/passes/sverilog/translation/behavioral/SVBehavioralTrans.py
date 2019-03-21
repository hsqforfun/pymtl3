#=========================================================================
# SVBehavioralTrans.py
#=========================================================================

from pymtl.passes.rtlir.translation.behavioral import BehavioralTrans

from SVBehavioralUpblkTrans import SVBehavioralUpblkTrans as SVUpblkTr
from SVBehavioralConstraintTrans\
    import SVBehavioralConstraintTrans as SVConstraintTr

class SVBehavioralTrans( BehavioralTrans, SVUpblkTr, SVConstraintTr ):

  def __init__( s, top ):

    super( SVBehavioralTrans, s ).__init__( top )

  def translate( s ):

    super( SVBehavioralTrans, s ).translate()
