#=========================================================================
# BehavioralUpblkTrans.py
#=========================================================================
# Translate upblk behavioral RTLIR into a specific backend.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from BaseBehavioralTrans     import BaseBehavioralTrans
from UpblkRTLIRGenPass       import UpblkRTLIRGenPass
from UpblkRTLIRTypeCheckPass import UpblkRTLIRTypeCheckPass
from ..utility               import gen_type_env

class BehavioralUpblkTrans( BaseBehavioralTrans ):

  # Override
  def __init__( s, top ):

    super( BehavioralUpblkTrans, s ).__init__( top )

    s.behavioral.upblks     = {}
    s.behavioral.upblk_srcs = {}
    s.behavioral.freevars   = {}
    s.behavioral.tmpvars    = {}

    s.gen_upblk_trans_metadata( top, gen_type_env( top ) )

  # Override
  def translate( s ):

    super( BehavioralUpblkTrans, s ).translate()

    s.translate_upblk_decls( s.top )

  #-----------------------------------------------------------------------
  # gen_upblk_trans_metadata
  #-----------------------------------------------------------------------

  def gen_upblk_trans_metadata( s, m, type_env ):

    m.apply( UpblkRTLIRGenPass() )
    m.apply( UpblkRTLIRTypeCheckPass( type_env ) )

    s.behavioral.upblks[m] = m._pass_upblk_rtlir_gen.rtlir_upblks

    s.behavioral.freevars[m] = m._pass_upblk_rtlir_type_check.rtlir_freevars

    s.behavioral.tmpvars[m] = m._pass_upblk_rtlir_type_check.rtlir_tmpvars

    for child in m.get_child_components():
      s.gen_upblk_trans_metadata( child, type_env )

  #-----------------------------------------------------------------------
  # translate_upblk_decls
  #-----------------------------------------------------------------------

  def translate_upblk_decls( s, m ):

    upblks = []

    for upblk in m.get_update_blocks():
      upblks.append(
        s.__class__.rtlir_tr_upblk_decl(
          m, upblk, s.behavioral.upblks[m][ upblk ]
        )
      )

    s.component[m].upblk_srcs = s.__class__.rtlir_tr_upblk_decls( upblks )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_upblk_decls( upblk_srcs ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_upblk_decl( m, upblk, rtlir_upblk ):
    raise NotImplementedError()
