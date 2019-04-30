#=========================================================================
# BehavioralRTLIRGenL5Pass.py
#=========================================================================
# This pass generates the L5 RTLIR of a given component.
#
# Author : Peitian Pan
# Date   : Oct 20, 2018

import inspect

from pymtl        import *
from pymtl.passes import BasePass, PassMetadata

from BehavioralRTLIRGenL4Pass import BehavioralRTLIRGeneratorL4

class BehavioralRTLIRGenL5Pass( BasePass ):

  def __call__( s, m ):
    """ generate RTLIR for all upblks of m """

    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()

    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}

    visitor = BehavioralRTLIRGeneratorL5( m )

    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] =\
          visitor.enter( blk, m.get_update_block_ast( blk ) )

#-------------------------------------------------------------------------
# BehavioralRTLIRGeneratorL5
#-------------------------------------------------------------------------
# The attribute operation has been handled at previous levels.

class BehavioralRTLIRGeneratorL5( BehavioralRTLIRGeneratorL4 ):

  def __init__( s, component ):

    super( BehavioralRTLIRGeneratorL5, s ).__init__( component )
