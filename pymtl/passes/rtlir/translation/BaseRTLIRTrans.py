#=========================================================================
# BaseRTLIRTrans.py
#=========================================================================
# Base class for the RTLIR translator.
#
# Author : Peitian Pan
# Date   : March 11, 2019

class BaseRTLIRTrans( object ):

  def __init__( s, top ):

    s.top = top

    s.component = {}
    s.hierarchy = TransMetadata()

    s.gen_base_rtlir_trans_metadata( s.top )

  def translate( s ):
    pass

  def gen_base_rtlir_trans_metadata( s, m ):

    s.component[m] = TransMetadata()

    for child in m.get_child_components():
      s.gen_base_rtlir_trans_metadata( child )

#-------------------------------------------------------------------------
# TransMetadata
#-------------------------------------------------------------------------

class TransMetadata( object ):
  def __init__( s ):
    pass
