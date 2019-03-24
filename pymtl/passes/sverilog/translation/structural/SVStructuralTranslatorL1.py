#=========================================================================
# SVStructuralTranslatorL1.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural import StructuralTranslatorL1

class SVStructuralTranslatorL1( StructuralTranslatorL1 ):

  # Data type strings

  @staticmethod
  def rtlir_tr_const_int_type():
    return 'localparam {name} = {value}'

  @staticmethod
  def rtlir_tr_const_int_fw_type( nbits ):
    return 'localparam {name} = {value}'

  @staticmethod
  def rtlir_tr_bit_type( nbits ):
    return {
      'dtype'    : 'logic',
      'vec_size' : '[{}:0]'.format( nbits-1 )
    }

  # Signal declaration strings

  @staticmethod
  def rtlir_tr_bit_slice( base_signal, start, stop, step ):
    if stop == start+1:
      # Bit indexing
      return '[{}]'.format( start )
    else:
      assert (step is None) or (step == 1)
      return '[{}:{}]'.format( stop-1, start )

  @staticmethod
  def rtlir_tr_port_decls( port_decls ):
    make_indent( port_decls, 1 )
    return ',\n'.join( port_decls )

  @staticmethod
  def rtlir_tr_port_decl( direction, name, Type ):
    return '{} {} {} {}'.format(
      direction, Type['dtype'], Type['vec_size'], name
    )

  @staticmethod
  def rtlir_tr_wire_decls( wire_decls ):
    make_indent( wire_decls, 1 )
    return '\n'.join( wire_decls )

  @staticmethod
  def rtlir_tr_wire_decl( name, Type ):
    return '{} {} {}'.format(
      Type['dtype'], Type['vec_Size'], name
    )

  @staticmethod
  def rtlir_tr_const_decls( const_decls ):
    make_indent( const_decls, 1 )
    return ',\n'.join( const_decls )

  @staticmethod
  def rtlir_tr_const_decl( name, Type, value ):
    return Type.format( **locals() )

  # Connection strings

  @staticmethod
  def rtlir_tr_connections( connections ):
    make_indent( connections, 1 )
    return '\n'.join( connections )

  @staticmethod
  def rtlir_tr_connection( wr_signal, rd_signal ):
    return 'assign {} = {};'.format( rd_signal, wr_signal )

  @staticmethod
  def rtlir_tr_component( component_nspace ):
    template =\
"""
module {module_name}
# (
{const_decls}
)
(
{port_decls}
);

{wire_decls}

{upblk_srcs}

endmodule
"""
    module_name = component_nspace.component_name
    const_decls = component_nspace.const_decls
    port_decls  = component_nspace.port_decls
    wire_decls  = component_nspace.wire_decls
    upblk_srcs  = component_nspace.upblk_srcs

    return template.format( **locals() )

  @staticmethod
  def rtlir_tr_component_name( component_name ):
    return component_name

  @staticmethod
  def rtlir_tr_var_name( signal_name ):
    return signal_name.replace( '[', '_' ).replace( ']', '_' )

