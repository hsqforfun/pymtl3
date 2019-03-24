#=========================================================================
# BaseRTLIRTranslator.py
#=========================================================================
# Base class for the RTLIR translator.
#
# Author : Peitian Pan
# Date   : March 11, 2019

class BaseRTLIRTranslator( object ):

  def __init__( s, top ):

    s.top = top

    s.component = {}
    s.hierarchy = TranslatorMetadata()

    s.gen_base_rtlir_trans_metadata( s.top )

  def gen_base_rtlir_trans_metadata( s, m ):

    s.component[m] = TranslatorMetadata()

    for child in m.get_child_components():
      s.gen_base_rtlir_trans_metadata( child )

#-------------------------------------------------------------------------
# TranslatorMetadata
#-------------------------------------------------------------------------

class TranslatorMetadata( object ):
  def __init__( s ):
    pass
