#=========================================================================
# BehavioralTranslatorL1.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 22, 2019

from pymtl.passes.rtlir import get_rtlir_type

from pymtl.passes.rtlir.behavioral.BehavioralRTLIRGenL1Pass\
    import BehavioralRTLIRGenL1Pass
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL1Pass\
    import BehavioralRTLIRTypeCheckL1Pass

from BehavioralTranslatorL0 import BehavioralTranslatorL0

class BehavioralTranslatorL1( BehavioralTranslatorL0 ):

  def __init__( s, top ):

    super( BehavioralTranslatorL1, s ).__init__( top )

    s.behavioral.rtlir = {}
    s.behavioral.freevars = {}
    s.behavioral.upblk_srcs = {}

    s.gen_behavioral_trans_metadata( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  def gen_behavioral_trans_metadata( s, m ):

    m.apply( BehavioralRTLIRGenL1Pass() )
    m.apply( BehavioralRTLIRTypeCheckL1Pass() )

    s.behavioral.rtlir[m] =\
        m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] =\
        m._pass_behavioral_rtlir_type_check.rtlir_freevars

  #-----------------------------------------------------------------------
  # gen_type_env
  #-----------------------------------------------------------------------
  # L1 assumes only the top component is in the component hierarchy.

  # def gen_type_env( s, top ):

    # def collect_type_env( m, type_env ):

      # m_type = get_rtlir_type( m )

      # type_env[ m ]

      # for name, rtype in m.get_all_properties():

        # type_env[ name ] = rtype

    # ret = {}

    # collect_type_env( top, ret )

    # return ret

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):

    # Generate behavioral RTLIR for component `m`

    upblk_srcs = []

    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:

        upblk_srcs.append( s.rtlir_tr_upblk_decl(
          m, blk, s.behavioral.rtlir[ m ][ blk ]
        ) )

    s.behavioral.upblk_srcs[m] = s.rtlir_tr_upblk_decls( upblk_srcs )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    raise NotImplementedError()

  def rtlir_tr_upblk_decl( s, m, upblk, rtlir_upblk ):
    raise NotImplementedError()
