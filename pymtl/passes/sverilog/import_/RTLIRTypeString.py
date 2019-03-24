#=========================================================================
# RTLIRTypeString.py
#=========================================================================
# This file includes functions that convert an RTLIR type into a dict
# which contains various string represenations of the type.

from pymtl.passes.rtlir import BaseBehavioralRTLIRType

#-------------------------------------------------------------------------
# Specialized type string functions
#-------------------------------------------------------------------------

def signal_type_str( Type ):
  ret = {
    'c_dim_size' : ''
  }
  ret.update( Type.type_str() )
  return ret

def array_type_str( Type ):
  sub_type_str = rtlir_to_str( Type.Type )
  ret = {
    'c_dim_size' : '[{}]'.format( Type.length ) + sub_type_str[ 'c_dim_size' ],
  }
  ret.update( Type.type_str() )

  total_vec_num = reduce( lambda x,y: x*y, ret['n_dim_size'], 1 )

  ret[ 'total_bits' ] = total_vec_num * ret[ 'nbits' ]

  return ret

def const_type_str( Type ):
  assert not Type.value is None, "Trying to declare a constant but did not\
provide initial value!"

  ret = {
    'c_dim_size' : ''
  }
  ret.update( Type.type_str() )

  return ret

def module_type_str( Type ):
  ret = {
    'c_dim_size' : ''
  }
  ret.update( Type.type_str() )

  return ret

def struct_type_str( Type ):
  ret = {
    'c_dim_size' : ''
  }
  ret.update( Type.type_str() )

  total_bits = 0

  for obj, Type in Type.type_env.iteritems():
    type_str = rtlir_to_str( Type )
    total_bits += type_str[ 'total_bits' ]

  ret['nbits'] = ret['total_bits'] = total_bits

  return ret

def dummy_type_str( Type ):
  return {}

#-------------------------------------------------------------------------
# Type string table and type string generation function
#-------------------------------------------------------------------------

rtlir_type_string = {
  'Signal'        : signal_type_str,
  'Array'         : array_type_str,
  'Const'         : const_type_str,
  'Bool'          : dummy_type_str,
  'Module'        : module_type_str,
  'Struct'        : struct_type_str,
  'Interface'     : dummy_type_str,
  'BaseRTLIRType' : dummy_type_str,
  'BaseAttr'      : dummy_type_str,
  'NoneType'      : dummy_type_str
}

def rtlir_to_str( Type ):
  assert isinstance( Type, BaseBehavioralRTLIRType )
  return rtlir_type_string[ str(Type) ]( Type )
