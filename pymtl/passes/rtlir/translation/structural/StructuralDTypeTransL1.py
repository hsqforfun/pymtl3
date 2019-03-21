#=========================================================================
# StructuralDTypeTransL1.py
#=========================================================================
# Translate the datatype of an object into its backend representation.
# APIs:
#   dtype_tr_get_member_type(obj): return the backend type representation
#                                  of obj which is a member of component
#
#   dtype_tr_signal(obj):          return the backend type representation
#                                  of obj which is a signal but not
#                                  necessarily a member of component
#
# Author : Peitian Pan
# Date   : March 19, 2019

from BaseStructuralTrans import BaseStructuralTrans

class StructuralDTypeTransL1( BaseStructuralTrans ):

  def __init__( s, top ):

    super( StructuralDTypeTransL1, s ).__init__( top )

    s.hierarchy.value_types = {}

  def translate( s ):

    super( StructuralDTypeTransL1, s ).translate()

  #-----------------------------------------------------------------------
  # is_BitsX
  #-----------------------------------------------------------------------

  @staticmethod
  def is_BitsX( Type ):

    try:
      if Type.__name__.startswith( 'Bits' ):
        try:
          n = int( Type.__name__[4:] )
          return True
        except:
          return False
    except:
      return False

    return False

  #-----------------------------------------------------------------------
  # dtype_tr_get_member_type
  #-----------------------------------------------------------------------

  def dtype_tr_get_member_type( s, obj ):

    Type = obj._dsl.Type

    if StructuralDTypeTransL1.is_BitsX( Type ):
      ret = s.__class__.rtlir_tr_bit_type( Type.nbits )
      s.hierarchy.value_types[ Type.__name__ ] = ret
      return ret

    else:
      return super( StructuralDTypeTransL1, s ).dtype_tr_get_type( Type )

  #-----------------------------------------------------------------------
  # dtype_tr_signal
  #-----------------------------------------------------------------------

  def dtype_tr_signal( s, obj ):

    Slice = obj._dsl.slice

    if not ( Slice is None ):
      # Bit slicing and bit indexing
      return s.__class__.rtlir_tr_bit_slice(
        s.dtype_tr_signal( obj._dsl.parent_obj ),
        Slice.start, Slice.stop, Slice.step
      )

    elif ('level' in obj._dsl.__dict__):
      # `obj` is an attribute of some component
      return s.__class__.rtlir_tr_signal_name( obj._dsl.my_name )

    else:
      return super( StructuralDTypeTransL1, s ).dtype_tr_signal( obj )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_bit_type( nbits ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_bit_slice( base_signal, start, stop, step ):
    raise NotImplementedError()
