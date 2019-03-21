#=========================================================================
# StructuralTrans.py
#=========================================================================
# The structural translator that inherits from all the base structural
# translators.
#
# Author : Peitian Pan
# Date   : March 19, 2019

from BaseStructuralTrans import DummyStructuralTrans
from StructuralDTypeTransL1 import StructuralDTypeTransL1
from StructuralDeclTransL1  import StructuralDeclTransL1
from StructuralConnectionTransL1 import StructuralConnectionTransL1

def mk_StructuralTrans(
    dtype_trans_level, decl_trans_level, connection_trans_level
  ):
  """
     Construct a BehavioralTrans from the three given levels. This
     allows incremental development and testing.
  """

  assert (0<=dtype_trans_level<=1) and (0<=decl_trans_level<=1)\
         and (0<=connection_trans_level<=1)

  _StructuralDTypeTrans = DummyStructuralTrans if dtype_trans_level==0\
                     else StructuralDTypeTransL1

  _StructuralDeclTrans =  DummyStructuralTrans if decl_trans_level==0\
                     else StructuralDeclTransL1

  _StructuralConnectionTrans = DummyStructuralTrans if connection_trans_level==0\
                          else StructuralConnectionTransL1

  class _StructuralTrans(
      _StructuralDTypeTrans, _StructuralDeclTrans, _StructuralConnectionTrans
    ):

    def __init__( s, top ):

      super( _StructuralTrans, s ).__init__( top )

    def translate( s ):

      super( _StructuralTrans, s ).translate()

  return _StructuralTrans

StructuralTrans = mk_StructuralTrans(
    dtype_trans_level=1, decl_trans_level=1, connection_trans_level=1
  )
