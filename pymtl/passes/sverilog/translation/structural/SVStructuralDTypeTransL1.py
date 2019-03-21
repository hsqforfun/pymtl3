#=========================================================================
# SVDataTypeTransL1.py
#=========================================================================

from pymtl.passes.rtlir.translation.structural import StructuralDTypeTransL1

class SVStructuralDTypeTransL1( StructuralDTypeTransL1 ):

  @staticmethod
  def rtlir_tr_bit_type( nbits ):
    return {
      'dtype'    : 'logic',
      'vec_size' : '[{}:0]'.format( nbits-1 )
    }

  @staticmethod
  def rtlir_tr_bit_slice( base_signal, start, stop, step ):
    if stop == start+1:
      # Bit indexing
      return '[{}]'.format( start )
    else:
      assert (step is None) or (step == 1)
      return '[{}:{}]'.format( stop-1, start )
