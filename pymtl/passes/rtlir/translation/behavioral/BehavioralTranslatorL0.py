#=========================================================================
# BehavioralTranslatorL0.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 22, 2019

from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata

class BehavioralTranslatorL0( BaseRTLIRTranslator ):

  def __init__( s, top ):

    super( BehavioralTranslatorL0, s ).__init__( top )

    s.behavioral = TranslatorMetadata()

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  def translate_behavioral( s, m ):

    pass
