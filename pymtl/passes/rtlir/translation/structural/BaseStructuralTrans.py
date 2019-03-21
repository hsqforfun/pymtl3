#=========================================================================
# BaseStructuralTrans.py
#=========================================================================
# Base classes for the RTLIR structural translators.
#
# Author : Peitian Pan
# Date   : March 19, 2019

from ..BaseRTLIRTrans import BaseRTLIRTrans, TransMetadata

class BaseStructuralTrans( BaseRTLIRTrans ):

  def __init__( s, top ):

    super( BaseStructuralTrans, s ).__init__( top )

    s.structural = TransMetadata()

  def translate( s ):

    super( BaseStructuralTrans, s ).translate()

class DummyStructuralTrans( BaseStructuralTrans ):

  def __init__( s, top ):

    super( DummyStructuralTrans, s ).__init__( top )

  def translate( s ):

    super( DummyStructuralTrans, s ).translate()
