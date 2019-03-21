#=========================================================================
# BaseBehavioralTrans.py
#=========================================================================
# Base classes for the RTLIR behavioral translators.
#
# Author : Peitian Pan
# Date   : March 19, 2019

from ..BaseRTLIRTrans import BaseRTLIRTrans, TransMetadata

class BaseBehavioralTrans( BaseRTLIRTrans ):

  def __init__( s, top ):

    super( BaseBehavioralTrans, s ).__init__( top )

    s.behavioral = TransMetadata()

  def translate( s ):

    super( BaseBehavioralTrans, s ).translate()

class DummyBehavioralTrans( BaseBehavioralTrans ):

  def __init__( s, top ):

    super( DummyBehavioralTrans, s ).__init__( top )

  def translate( s ):

    super( DummyBehavioralTrans, s ).translate()
