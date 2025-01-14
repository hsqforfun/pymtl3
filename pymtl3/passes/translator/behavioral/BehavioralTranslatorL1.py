#=========================================================================
# BehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 22, 2019
"""Provide L1 behavioral translator."""


from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL1Pass import (
    BehavioralRTLIRGenL1Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL1Pass import (
    BehavioralRTLIRTypeCheckL1Pass,
)

from .BehavioralTranslatorL0 import BehavioralTranslatorL0


class BehavioralTranslatorL1( BehavioralTranslatorL0 ):
  def __init__( s, top ):
    super().__init__( top )

  def clear( s, tr_top ):
    super().clear( tr_top )
    s.gen_behavioral_trans_metadata( tr_top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  def gen_behavioral_trans_metadata( s, tr_top ):
    s.behavioral.rtlir = {}
    s.behavioral.freevars = {}
    s.behavioral.accessed = {}
    s.behavioral.upblk_decls = {}
    s.behavioral.upblk_srcs = {}
    s.behavioral.upblk_py_srcs = {}
    s.behavioral.decl_freevars = {}
    s._gen_behavioral_trans_metadata( tr_top )

  #-----------------------------------------------------------------------
  # _gen_behavioral_trans_metadata
  #-----------------------------------------------------------------------

  def _gen_behavioral_trans_metadata( s, m ):
    m.apply( BehavioralRTLIRGenL1Pass() )
    m.apply( BehavioralRTLIRTypeCheckL1Pass() )
    s.behavioral.rtlir[m] = \
        m._pass_behavioral_rtlir_gen.rtlir_upblks
    s.behavioral.freevars[m] = \
        m._pass_behavioral_rtlir_type_check.rtlir_freevars

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  # Override
  def translate_behavioral( s, m ):
    """Translate behavioral part of `m`."""
    # Get upblk metadata
    s.behavioral.accessed[m] = m._pass_behavioral_rtlir_type_check.rtlir_accessed
    # Translate upblks
    upblk_decls = []
    upblk_srcs = []
    upblk_py_srcs = []
    upblks = {
      'CombUpblk' : list(m.get_update_blocks() - m.get_update_ff()),
      'SeqUpblk'  : list(m.get_update_ff())
    }
    # Sort the upblks by their name
    upblks['CombUpblk'].sort( key = lambda x: x.__name__ )
    upblks['SeqUpblk'].sort( key = lambda x: x.__name__ )

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        upblk_ir = s.behavioral.rtlir[ m ][ blk ]
        upblk_srcs.append( s.rtlir_tr_upblk_src(
          blk, upblk_ir
        ) )
        upblk_py_srcs.append( s.rtlir_tr_upblk_py_src(
          blk,
          upblk_ir.is_lambda,
          upblk_ir.src,
          upblk_ir.lino,
          upblk_ir.filename
        ) )
        upblk_decls.append( s.rtlir_tr_upblk_decl(
          blk, upblk_srcs[-1], upblk_py_srcs[-1]
        ) )
    s.behavioral.upblk_srcs[m] = s.rtlir_tr_upblk_srcs( upblk_srcs )
    s.behavioral.upblk_py_srcs[m] = s.rtlir_tr_upblk_decls( upblk_py_srcs )
    s.behavioral.upblk_decls[m] = s.rtlir_tr_upblk_decls( upblk_decls )

    # Generate free variable declarations
    freevars = []
    for name, fvar in s.behavioral.freevars[m].items():
      rtype = rt.get_rtlir( fvar )
      if isinstance( rtype, rt.Array ):
        fvar_rtype = rtype.get_sub_type()
        array_rtype = rtype
      else:
        fvar_rtype = rtype
        array_rtype = None
      dtype = fvar_rtype.get_dtype()
      assert isinstance( dtype, rdt.Vector ), \
        f'{name} freevar should be an integer or a list of integers!'
      freevars.append( s.rtlir_tr_behavioral_freevar(
        name,
        fvar_rtype,
        s.rtlir_tr_unpacked_array_type( array_rtype ),
        s.rtlir_tr_vector_dtype( dtype ),
        fvar
      ) )
    s.behavioral.decl_freevars[m] = s.rtlir_tr_behavioral_freevars(freevars)

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  def rtlir_tr_upblk_decls( s, upblk_decls ):
    raise NotImplementedError()

  def rtlir_tr_upblk_decl( s, upblk, src, py_src ):
    raise NotImplementedError()

  def rtlir_tr_upblk_srcs( s, upblk_srcs ):
    raise NotImplementedError()

  def rtlir_tr_upblk_src( s, upblk, rtlir_upblk ):
    raise NotImplementedError()

  def rtlir_tr_upblk_py_srcs( s, upblk_py_srcs ):
    raise NotImplementedError()

  def rtlir_tr_upblk_py_src( s, upblk, is_lambda, src, lino, filename ):
    raise NotImplementedError()

  def rtlir_tr_behavioral_freevars( s, freevars ):
    raise NotImplementedError()

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    raise NotImplementedError()
