#=========================================================================
# SVStructuralTranslatorL1.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL1\
    import StructuralTranslatorL1

class SVStructuralTranslatorL1( StructuralTranslatorL1 ):

  # Data types

  def rtlir_tr_vector_dtype( s, Type ):
    msb = Type.get_length() -1
    return {
      'def'  : '',
      'decl' : 'logic [{msb}:0] {{name}}'.format( **locals() )
    }

  def rtlir_tr_array_dtype( s, Type, subtype ):
    item_dtype = subtype['decl']
    array_dim = reduce(
      lambda x,y: x+'[0:{}]'.format(y-1), Type.get_dim_sizes(), ''
    )
    return {
      'def'  : '',
      'decl' : item_dtype + ' ' + array_dim
    }

  # Declarations
  
  def rtlir_tr_port_decls( s, port_decls ):
    make_indent( port_decls, 1 )
    return ',\n'.join( port_decls )
  
  def rtlir_tr_port_decl( s, name, Type, dtype ):
    return Type.get_direction() + ' ' + dtype['decl'].format( **locals() )
  
  def rtlir_tr_wire_decls( s, wire_decls ):
    make_indent( wire_decls, 1 )
    return '\n'.join( wire_decls )
  
  def rtlir_tr_wire_decl( s, name, Type, dtype ):
    return dtype['decl'].format( **locals() ) + ';'
  
  def rtlir_tr_const_decls( s, const_decls ):
    make_indent( const_decls, 1 )
    return '\n'.join( const_decls )
  
  def rtlir_tr_const_decl( s, name, Type, dtype, value ):

    assert isinstance( dtype, Vector ),\
      '{} is not a vector constant!'.format( value )

    value = int( value )

    return 'localparam {name} = {value};'.format( **locals() )

  # Connections
  
  def rtlir_tr_connections( s, connections ):
    make_indent( connections, 1 )
    return '\n'.join( connections )
  
  def rtlir_tr_connection( s, wr_signal, rd_signal ):
    return 'assign {rd_signal} = {wr_signal};'.format( **locals() )

  # Signal operations
  
  def rtlir_tr_bit_selection( s, base_signal, index ):
    # Bit selection
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_part_selection( s, base_signal, start, stop, step ):
    # Part selection
    assert (step is None) or (step == 1)
    _stop = stop-1
    return '{base_signal}[{_stop}:{start}]'.format( **locals() )

  # Miscs

  def rtlir_tr_var_name( s, signal_name ):
    return signal_name.replace( '[', '_' ).replace( ']', '_' )

  def rtlir_tr_literal_number( s, value, nbits ):
    return "{nbits}'d{value}".format( **locals() )
