#=========================================================================
# SVStructuralTranslatorL1.py
#=========================================================================

import pymtl
from pymtl.passes.utility import make_indent, get_string
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL1\
    import StructuralTranslatorL1
from pymtl.passes.rtlir.RTLIRType import *

class SVStructuralTranslatorL1( StructuralTranslatorL1 ):

  # Data types

  def rtlir_tr_vector_dtype( s, Type ):
    msb = Type.get_length() - 1
    return {
      'def'  : '',
      'nbits' : Type.get_length(),
      'const_decl' : '[{msb}:0] {{id_}}'.format( **locals() ),
      'decl' : 'logic [{msb}:0] {{id_}}'.format( **locals() )
    }

  def rtlir_tr_unpacked_array_type( s, Type ):
    if Type is None: return { 'def' : '', 'decl' : '', 'n_dim':[] }

    else:
      array_dim = reduce(
        lambda x,y: x+'[0:{}]'.format(y-1), Type.get_dim_sizes(), ''
      )
      return {
        'def'  : '',
        'decl' : array_dim,
        'n_dim' : Type.get_dim_sizes()
      }

  # Declarations
  
  def rtlir_tr_port_decls( s, port_decls ):
    make_indent( port_decls, 1 )
    return ',\n'.join( port_decls )
  
  def rtlir_tr_port_decl( s, id_, Type, array_type, dtype ):
    return Type.get_direction() + ' ' +\
           dtype['decl'].format( **locals() ) + ' ' +\
           array_type['decl']
  
  def rtlir_tr_wire_decls( s, wire_decls ):
    make_indent( wire_decls, 1 )
    return '\n'.join( wire_decls )
  
  def rtlir_tr_wire_decl( s, id_, Type, array_type, dtype ):
    return dtype['decl'].format( **locals() ) + ' ' + \
           array_type['decl'] + ';'
  
  def rtlir_tr_const_decls( s, const_decls ):
    make_indent( const_decls, 1 )
    return '\n'.join( const_decls )
  
  def rtlir_tr_const_decl( s, id_, Type, array_type, dtype, value ):

    def gen_array_param( n_dim, array ):

      if not n_dim:

        assert not isinstance( array, list )

        if isinstance( array, pymtl.Bits ):
          return s.rtlir_tr_literal_number( array.nbits, array.value )

        elif isinstance( array, int ):
          return s.rtlir_tr_literal_number( 32, array )

        else: assert False, '{} is not an integer!'.format( array )

      assert isinstance( array, list )

      ret = '{'
      for _idx, idx in enumerate( xrange( n_dim[0] ) ):
        if _idx != 0: ret += ','
        ret += gen_array_param( n_dim[1:], array[idx] )
      ret += '}'

      return ret

    assert isinstance( Type.get_dtype(), Vector ),\
      '{} is not a vector constant!'.format( value )

    nbits = dtype['nbits']

    _dtype = dtype['const_decl'].format( **locals() ) + array_type['decl']

    _value = gen_array_param( array_type['n_dim'], value )

    return 'localparam {_dtype} = {_value};'.format( **locals() )

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

  def rtlir_tr_part_selection( s, base_signal, start, stop ):
    # Part selection
    _stop = stop-1
    return '{base_signal}[{_stop}:{start}]'.format( **locals() )

  def rtlir_tr_port_array_index( s, base_signal, index ):
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_wire_array_index( s, base_signal, index ):
    return '{base_signal}[{index}]'.format( **locals() )

  def rtlir_tr_const_array_index( s, base_signal, index ):
    return '{base_signal}[{index}]'.format( **locals() )

  # def rtlir_tr_unpacked_index( s, base_signal, index ):
    # # Index operation of an unpacked array
    # return '{base_signal}_${index}'.format( **locals() )

  def rtlir_tr_current_comp_attr( s, base_signal, attr ):
    return '{attr}'.format( **locals() )

  def rtlir_tr_current_comp( s, comp_id, comp_rtype ):
    return ''

  # Miscs

  def rtlir_tr_var_id( s, var_id ):
    return var_id.replace( '[', '_$' ).replace( ']', '' )

  def rtlir_tr_literal_number( s, nbits, value ):
    return "{nbits}'d{value}".format( **locals() )

  def rtlir_tr_component_unique_name( s, c_rtype ):
    comp_name = c_rtype.get_name()
    comp_params = c_rtype.get_params()
    comp_argspec = c_rtype.get_argspec()

    assert comp_name and comp_params

    # Add const args to module name

    for idx, arg_name in enumerate( comp_argspec.args[1:] ):

      arg_value = comp_params[ '' ][idx]
      comp_name += '__' + arg_name + '_' + get_string(arg_value)

    # Add varargs to module name

    if len( comp_params[''] ) > len( comp_argspec.args[1:] ):

      comp_name += '__' + comp_argspec.varargs
    
    for arg_value in comp_params[''][ len(comp_argspec.args[1:]): ]:

      comp_name += '___' + get_string(arg_value)

    # Add kwargs to module name

    for arg_name, arg_value in comp_params.iteritems():

      if arg_name == '': continue
      comp_name += '__' + arg_name + '_' + get_string(arg_value)

    return comp_name
