#=========================================================================
# utility.py
#=========================================================================
# This file includes the helper functions that might be useful for
# translation or other passes.
#
# Author : Peitian Pan
# Date   : Feb 22, 2019

import inspect

from pymtl                        import *

from pymtl.passes.rtlir           import get_type
from pymtl.passes.utility         import *
from pymtl.passes.rtlir.RTLIRType import Struct, BaseRTLIRType

from RTLIRTypeString import rtlir_to_str

#-------------------------------------------------------------------------
# generate_interface_decl
#-------------------------------------------------------------------------

def generate_interface_decl( name, Type ):

  type_str = Type.type_str()
  if type_str['py_type'] == 'InVPort':
    prefix = 'input'
  elif type_str['py_type'] == 'OutVPort':
    prefix = 'output'
  else:
    assert False, "only input and output value ports are supported now"

  return prefix + ' ' + generate_signal_decl_from_type( name, Type )

#-------------------------------------------------------------------------
# generate_signal_decl
#-------------------------------------------------------------------------
# Generate a string that conforms to SystemVerilog style signal
# declaration of `port`, and displays its name as `name`.

def generate_signal_decl( name, port ):

  return generate_signal_decl_from_type( name, get_type( port ) )

#-------------------------------------------------------------------------
# generate_signal_decl_from_type
#-------------------------------------------------------------------------

def generate_signal_decl_from_type( name, Type ):

  name = get_verilog_name( name )

  type_str = rtlir_to_str( Type )

  return '{dtype} {vec_size} {name} {dim_size}'.format(
    dtype = type_str[ 'dtype' ], vec_size = type_str[ 'vec_size' ],
    name = name,                 dim_size = type_str[ 'dim_size' ]
  )

#-------------------------------------------------------------------------
# generate_struct_def
#-------------------------------------------------------------------------
# Generate the definition for a single struct object

def generate_struct_def( name, Type ):

  template = """typedef struct packed {{
{defs} 
}} {name};
"""

  defs = []
  type_str = rtlir_to_str( Type )

  # generate declarations for each field in the struct
  for _obj, _Type in Type.pack_order:
    defs.append(
      generate_signal_decl( get_verilog_name( _obj._dsl.my_name ), _obj ) + ';'
    )

  make_indent( defs, 1 )

  return template.format(
    defs = '\n'.join( defs ), name = type_str[ 'dtype' ]
  )

#-------------------------------------------------------------------------
# is_param_equal
#-------------------------------------------------------------------------

def is_param_equal( src, dst ):

  if len( src[''] ) != len( dst[''] ): return False
  if src.keys() != dst.keys(): return False

  for s, d in zip( src[''], dst[''] ):
    if s != d:
      return False

  for key in src.keys():
    if key == '': continue
    if src[key] != dst[key]:
      return False

  return True

#-------------------------------------------------------------------------
# get_verilog_name
#-------------------------------------------------------------------------

def get_verilog_name( name ):
  return name.replace( '[', '__' ).replace( ']', '__' )
