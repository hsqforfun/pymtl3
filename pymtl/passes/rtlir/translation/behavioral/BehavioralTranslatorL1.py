#=========================================================================
# BehavioralTranslatorL1.py
#=========================================================================
#
# Author : Peitian Pan
# Date   : March 22, 2019

import ast

from ..utility import *
from ..BaseRTLIRTranslator import BaseRTLIRTranslator, TranslatorMetadata

from BehavioralRTLIRGenL1Pass import BehavioralRTLIRGenL1Pass
from BehavioralRTLIRTypeCheckL1Pass import BehavioralRTLIRTypeCheckL1Pass

from BehavioralRTLIR       import *
from BehavioralRTLIRTypeL1 import BaseBehavioralRTLIRType
from errors                import PyMTLSyntaxError

class BehavioralTranslatorL1( BaseRTLIRTranslator ):

  def __init__( s, top ):

    super( BehavioralTranslatorL1, s ).__init__( top )

    s.behavioral = TranslatorMetadata()

    s.behavioral.rtlir = {}
    s.behavioral.type_env = s.gen_type_env( top )

    s.gen_behavioral_trans_l1_metadata( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_l1_metadata
  #-----------------------------------------------------------------------

  def gen_behavioral_trans_l1_metadata( s, m ):

    m.apply( BehavioralRTLIRGenL1Pass() )
    m.apply( BehavioralRTLIRTypeCheckL1Pass( s.behavioral.type_env ) )

    s.behavioral.rtlir[m] = m._pass_behavioral_rtlir_gen.rtlir_upblks

  #-----------------------------------------------------------------------
  # gen_type_env
  #-----------------------------------------------------------------------
  # L1 assumes only the top component in the component hierarchy.

  def gen_type_env( s, m ):

    ret = {}

    Type = BaseBehavioralRTLIRType.get_type( m )

    ret[ m ] = Type

    ret.update( Type.type_env )

    return ret

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  def translate_behavioral( s, m ):

    # Generate behavioral RTLIR for component `m`

    upblk_srcs = []

    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:

        upblk_srcs.append( s.__class__.rtlir_tr_upblk_decl(
          m, blk, s.behavioral.rtlir[m][ blk ]
        ) )

    s.component[ m ].upblk_srcs =\
        s.__class__.rtlir_tr_upblk_decls( upblk_srcs )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_upblk_decls( upblk_srcs ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_upblk_decl( m, upblk, rtlir_upblk ):
    raise NotImplementedError()
