#=========================================================================
# SVBehavioralConstraintTrans.py
#=========================================================================
# Provide the actual backend implementation of all virtual methods defined
# in ConstraintTrans.py.
# Author : Peitian Pan
# Date   : March 18, 2019

from pymtl.passes.rtlir.translation.behavioral import BehavioralConstraintTrans

class SVBehavioralConstraintTrans( BehavioralConstraintTrans ):

  @staticmethod
  def rtlir_tr_constraints( constraints ):
    ret = ""
    ret = '\n'.join( constraints )
    return ret

  @staticmethod
  def rtlir_tr_constraint( in_strs, conn_strs, out_str ):
    _in_strs = map( lambda x: x[1]+x[0], zip( in_strs, conn_strs ) )
    return ', '.join( _in_strs ) + ' => ' + out_str
