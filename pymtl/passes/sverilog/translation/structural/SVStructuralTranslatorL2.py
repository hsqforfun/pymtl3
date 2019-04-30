#=========================================================================
# SVStructuralTranslatorL2.py
#=========================================================================

from pymtl.passes.sverilog.utility import make_indent
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL2\
    import StructuralTranslatorL2
from pymtl.passes.rtlir.RTLIRType import *

from SVStructuralTranslatorL1 import SVStructuralTranslatorL1

class SVStructuralTranslatorL2(
    SVStructuralTranslatorL1, StructuralTranslatorL2
  ):

  # Data types

  def rtlir_tr_struct_dtype( s, Type ):
    dtype_name = Type.get_name()

    field_decls = []

    for id_, rtype in Type.get_all_properties():

      if isinstance( rtype, Vector ):

        decl = s.rtlir_tr_vector_dtype( rtype )['decl'].format(**locals())

      elif isinstance( rtype, Array ):

        decl = s.rtlir_tr_array_dtype( rtype )['decl'].format(**locals())

      elif isinstance( rtype, Struct ):

        decl = s.rtlir_tr_struct_dtype( rtype )['decl'].format(**locals())

      else: assert False,\
        'unrecoganized field type {} of struct {}!'.format( rtype, dtype_name )

      field_decls.append( decl + ';' )

    make_indent( field_decls, 1 )

    field_decl = '\n'.join( field_decls )

    return {
      'def'  :\
        'typedef struct packed {{\n{field_decl}\n}} {dtype_name};\n'.format(
          **locals()
        ),
      'decl' : '{dtype_name} {{id_}}'.format( **locals() )
    }

  # Signal oeprations

  def rtlir_tr_packed_index( s, base_signal, index ):
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_struct_attr( s, base_signal, attr ):
    return '{base_signal}.{attr}'.format( **locals() )
