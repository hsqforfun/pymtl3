#=========================================================================
# SVStructuralTranslatorL2.py
#=========================================================================
"""Provide SystemVerilog structural translator implementation."""

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.sverilog.util.utility import make_indent
from pymtl3.passes.translator.structural.StructuralTranslatorL2 import (
    StructuralTranslatorL2,
)

from .SVStructuralTranslatorL1 import SVStructuralTranslatorL1


class SVStructuralTranslatorL2(
    SVStructuralTranslatorL1, StructuralTranslatorL2 ):

  #-----------------------------------------------------------------------
  # Data types
  #-----------------------------------------------------------------------

  def rtlir_tr_packed_array_dtype( s, dtype ):
    sub_dtype = dtype.get_sub_dtype()
    if isinstance( sub_dtype, rdt.Vector ):
      sub_dtype_template = s.rtlir_tr_vector_dtype( sub_dtype )
    elif isinstance( sub_dtype, rdt.Struct ):
      sub_dtype_template = s.rtlir_tr_struct_dtype( sub_dtype )
    else:
      raise Exception(f"unsupported data type {sub_dtype} in packed array!")
    dim_str = "".join( f"[{size-1}:0]" for size in dtype.get_dim_sizes() )
    str_list = sub_dtype_template['decl'].split()
    if '[' in str_list[-2]:
      str_list[-2] = dim_str + str_list[-2]
    else:
      str_list = str_list[:-1] + [ dim_str ] + [ str_list[-1] ]
    return {
      'def' : '',
      'const_decl' : ' '.join( str_list ),
      'decl' : ' '.join( str_list ),
      'ndim' : dtype.get_dim_sizes(),
      'raw_dtype' : dtype
    }

  def rtlir_tr_struct_dtype( s, dtype ):
    dtype_name = dtype.get_name()
    field_decls = []

    for id_, _dtype in dtype.get_all_properties().items():

      if isinstance( _dtype, rdt.Vector ):
        decl = s.rtlir_tr_vector_dtype( _dtype )['decl'].format(**locals())
      elif isinstance( _dtype, rdt.PackedArray ):
        decl = s.rtlir_tr_packed_array_dtype( _dtype )['decl'].format(**locals())
      elif isinstance( _dtype, rdt.Struct ):
        decl = s.rtlir_tr_struct_dtype( _dtype )['decl'].format(**locals())
      else:
        assert False, \
          f'unrecoganized field type {_dtype} of struct {dtype_name}!'
      field_decls.append( decl + ';' )

    make_indent( field_decls, 1 )
    field_decl = '\n'.join( field_decls )

    file_info = dtype.get_file_info()

    return {
      'def' : \
f"""\
typedef struct packed {{
{field_decl}
}} {dtype_name};
""",
      'const_decl' : f'{dtype_name} {{id_}}',
      'decl' : f'{dtype_name} {{id_}}',
      'raw_dtype' : dtype
    }

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  def gen_array_param( s, n_dim, dtype, array ):
    if not n_dim:
      if isinstance( dtype, rdt.Struct ):
        return s.rtlir_tr_struct_instance( dtype, array )
      else:
        return super().gen_array_param( n_dim, dtype, array )
    else:
      return super().gen_array_param( n_dim, dtype, array )

  #-----------------------------------------------------------------------
  # Signal oeprations
  #-----------------------------------------------------------------------

  def rtlir_tr_packed_index( s, base_signal, index ):
    return f'{base_signal}[{index}]'

  def rtlir_tr_struct_attr( s, base_signal, attr ):
    return f'{base_signal}.{attr}'

  def rtlir_tr_struct_instance( s, dtype, struct ):
    def _gen_packed_array( dtype, n_dim, array ):
      if not n_dim:
        if isinstance( dtype, rdt.Vector ):
          return s.rtlir_tr_literal_number( dtype.nbits, array )
        elif isinstance( dtype, rdt.Struct ):
          return s.rtlir_tr_struct_instance( dtype, array )
        else:
          raise Exception(f"unrecognized data type {dtype}!")
      else:
        ret = []
        for i in reversed( range( n_dim[0]) ):
          ret.append( _gen_packed_array( dtype, n_dim[1:], array[i] ) )
        if n_dim[0] > 1:
          cat_str = "{" + ", ".join( ret ) + "}"
        else:
          cat_str = ", ".join( ret )
        return f"{{ {cat_str} }}"
    ret = []
    for name, Type in dtype.get_all_properties().items():
      field = getattr( struct, name )
      if isinstance( Type, rdt.Vector ):
        _ret = s.rtlir_tr_literal_number( Type.nbits, field )
      elif isinstance( Type, rdt.Struct ):
        _ret = s.rtlir_tr_struct_instance( Type, field )
      elif isinstance( Type, rdt.PackedArray ):
        n_dim = Type.get_dim_sizes()
        sub_dtype = Type.get_sub_dtype()
        _ret = _gen_packed_array( sub_dtype, n_dim, field )
      else:
        assert False, f"unrecognized data type {Type}!"
      ret.append( _ret )
    cat_str = ", ".join( ret )
    return f"{{ {cat_str} }}"
